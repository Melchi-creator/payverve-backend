"""Accepting payment on behalf of a shop.

A merchant is a Payverve user wearing a second hat. Settlement goes to the
owner's own NGN wallet, and the account a buyer transfers to is the owner's
BellBank virtual account, so no new money-holding entity is introduced here.

Two ways to pay a charge:

  wallet    an internal ledger move between two Payverve wallets, authorised
            by the buyer's transaction pin. Touches no bank and no provider.

  transfer  the buyer is shown the merchant's BellBank account number and a
            countdown, and pays from any bank app. Settlement is recognised
            when BellBank's collection webhook credits the merchant, which is
            matched back to the charge by amount and window.

Functions here stage work in the session and do not commit, matching
services/registration.py: the caller owns the transaction.
"""
import ipaddress
import secrets
import socket
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import urlencode, urlsplit, urlunsplit

from ..models import (ChargeModel, MerchantModel, PayverveTransferModel,
                      TransactionModel, VirtualAccountNumberModel, WalletModel,
                      db)
from ..models.charge import (CHARGE_TTL_SECONDS, PAID, PAID_BY_WALLET,
                             PENDING)
from ..utilities import (Cryptographer, encrypt_identifier,
                         hash_identifier)
from .registration import RegistrationError

PUBLIC_KEY_PREFIX = 'pk'
SECRET_KEY_PREFIX = 'sk'


def _key(prefix):
    """A key with an obvious prefix, so a leaked one is recognisable on sight."""
    mode = 'test' if _is_test_mode() else 'live'
    return f'{prefix}_{mode}_{secrets.token_hex(24)}'


def _is_test_mode():
    import config
    return bool(getattr(config, 'is_dev', False))


def issue_keys():
    """A fresh key pair.

    Returns (public_key, secret_key, secret_key_hash, preview). The secret is
    returned to the caller once and must never be stored: only the hash is.
    """
    public_key = _key(PUBLIC_KEY_PREFIX)
    secret_key = _key(SECRET_KEY_PREFIX)
    return (public_key, secret_key, hash_identifier(secret_key),
            secret_key[-4:])


def merchant_for_secret(secret_key):
    """The active merchant a secret key belongs to, or None.

    Looked up by keyed hash: the plaintext secret is never in the database, so
    a leaked dump cannot be used to charge on a merchant's behalf.
    """
    if not secret_key:
        return None

    return MerchantModel.query.filter_by(
        secret_key_hash=hash_identifier(secret_key.strip()),
        is_active=True).first()


def stage_merchant(user, business_name, webhook_url=None):
    """Register a shop for `user`. Does not commit.

    Returns (merchant, secret_key, webhook_secret) -- the only moment either
    secret exists in plaintext.
    """
    name = (business_name or '').strip()

    if not name:
        raise RegistrationError(400, 'bad request',
                                'a business name is required')

    if MerchantModel.query.filter_by(user_id=user.id, is_active=True).first():
        raise RegistrationError(409, 'conflict',
                                'this account already has a merchant profile')

    webhook_url = clean_webhook_url(webhook_url)
    public_key, secret_key, secret_hash, preview = issue_keys()

    # Signs outgoing webhooks. Encrypted rather than hashed: we must recover
    # the plaintext to compute a signature, unlike the secret key, which we
    # only ever compare.
    webhook_secret = _new_webhook_secret()

    # noinspection PyArgumentList
    merchant = MerchantModel(
        business_name=name,
        public_key=public_key,
        secret_key_hash=secret_hash,
        secret_key_preview=preview,
        webhook_url=webhook_url,
        webhook_secret=encrypt_identifier(webhook_secret),
        user_id=user.id,
    )
    db.session.add(merchant)
    return merchant, secret_key, webhook_secret


def _new_webhook_secret():
    return f'whsec_{secrets.token_hex(24)}'


def _blocked_address(address):
    """True for an address our server must never be made to post to:
    loopback, private networks, link-local (cloud metadata lives at
    169.254.169.254), and the like."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return not ip.is_global


def _allow_local_targets():
    import config
    return bool(getattr(config, 'is_dev', False))


def webhook_host_is_public(url):
    """Resolve the webhook's host and refuse any non-public address.

    Checked again at every delivery, not only at registration: a name that
    pointed at a public address when the shop saved it can be repointed at
    our own internal network afterwards.
    """
    if _allow_local_targets():
        return True

    host = urlsplit(url).hostname

    if not host:
        return False

    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False

    addresses = {info[4][0] for info in infos}
    return bool(addresses) and not any(_blocked_address(a) for a in addresses)


def clean_webhook_url(webhook_url):
    """An https URL to a public host, or None to switch webhooks off.

    Our server posts payment events to this address, so it must not be a
    way to make Payverve call its own internal network (SSRF). https only,
    because the body says which order was paid. Development allows http and
    localhost so a developer can receive webhooks on their own machine.
    """
    webhook_url = (webhook_url or '').strip()

    if not webhook_url:
        return None

    parts = urlsplit(webhook_url)
    local_ok = _allow_local_targets()
    schemes = ('https', 'http') if local_ok else ('https',)
    host = (parts.hostname or '').lower()

    if parts.scheme not in schemes or not host or len(webhook_url) > 2000:
        raise RegistrationError(400, 'bad request',
                                'webhook_url must be an https url')

    if not local_ok and (host == 'localhost' or host.endswith('.localhost')
                         or host.endswith('.internal')
                         or _blocked_address(host.strip('[]'))):
        raise RegistrationError(400, 'bad request',
                                'webhook_url must be a public address')
    return webhook_url


def _check_owner_pin(user, transaction_pin):
    """Changing a shop's keys or where its payment events go needs the
    owner's transaction pin, not just a session: a stolen login token must not
    be enough to cut a shop off or read its order traffic."""
    if not user.transaction_pin:
        raise RegistrationError(400, 'bad request',
                                'set a transaction pin first')

    if not transaction_pin or             not user.check_transaction_pin(str(transaction_pin)):
        raise RegistrationError(400, 'bad request', 'incorrect transaction pin')


def rotate_secret_key(merchant, user, transaction_pin):
    """Replace the shop's secret key. Does not commit.

    The old key stops working the moment this commits -- that is the point
    when a key has leaked -- so the shop's server must be updated straight
    away. The public key is kept: it only identifies the shop.
    Returns the new secret, the only time it exists in plaintext.
    """
    _check_owner_pin(user, transaction_pin)
    _, secret_key, secret_hash, preview = issue_keys()
    merchant.secret_key_hash = secret_hash
    merchant.secret_key_preview = preview
    db.session.add(merchant)
    return secret_key


def rotate_webhook_secret(merchant, user, transaction_pin):
    """Replace the secret webhooks are signed with. Does not commit.

    Deliveries are signed when sent, not when queued, so retries still
    pending go out signed with the new secret.
    """
    _check_owner_pin(user, transaction_pin)
    webhook_secret = _new_webhook_secret()
    merchant.webhook_secret = encrypt_identifier(webhook_secret)
    db.session.add(merchant)
    return webhook_secret


def update_webhook_url(merchant, user, transaction_pin, webhook_url):
    """Point payment events somewhere else, or nowhere. Does not commit.

    Events already queued keep the address they were queued with: an event
    that has happened is delivered where the shop said at the time.
    Returns a new webhook secret if the shop never had one, else None.
    """
    _check_owner_pin(user, transaction_pin)
    merchant.webhook_url = clean_webhook_url(webhook_url)
    issued = None

    if merchant.webhook_url and not merchant.webhook_secret:
        issued = _new_webhook_secret()
        merchant.webhook_secret = encrypt_identifier(issued)

    db.session.add(merchant)
    return issued


def stage_charge(merchant, reference, amount, callback_url=None,
                 currency_ticker='ngn'):
    """Create, or return, the charge for `reference`. Does not commit.

    Creating a charge is idempotent on the merchant's own reference: a shop
    retrying the call gets the same charge back rather than a second one the
    buyer could also pay.
    """
    reference = (reference or '').strip()

    if not reference:
        raise RegistrationError(400, 'bad request',
                                'a reference is required')

    try:
        value = Decimal(str(amount))
    except Exception:
        raise RegistrationError(400, 'bad request',
                                'amount must be a number')

    if value <= 0:
        raise RegistrationError(400, 'bad request',
                                'amount must be greater than zero')

    callback_url = clean_callback_url(callback_url)

    existing = ChargeModel.query.filter_by(
        merchant_id=merchant.id, reference=reference).first()

    if existing:
        return existing

    # noinspection PyArgumentList
    charge = ChargeModel(
        reference=reference,
        charge_code=secrets.token_urlsafe(18),
        amount=value.quantize(Decimal('0.01')),
        currency_ticker=(currency_ticker or 'ngn').lower(),
        status=PENDING,
        callback_url=callback_url,
        expires_at=datetime.now() + timedelta(seconds=CHARGE_TTL_SECONDS),
        merchant_id=merchant.id,
    )
    db.session.add(charge)
    return charge


def clean_callback_url(callback_url):
    """An http(s) URL, or None. Refuses anything else.

    The checkout page sends the buyer's browser here once the charge is paid.
    Anything but http(s) -- javascript:, data:, a bare path -- would run in, or
    be resolved against, Payverve's own page, so it is refused at creation
    rather than trusted at redirect.
    """
    callback_url = (callback_url or '').strip()

    if not callback_url:
        return None

    parts = urlsplit(callback_url)

    if parts.scheme not in ('http', 'https') or not parts.netloc             or len(callback_url) > 2000:
        raise RegistrationError(400, 'bad request',
                                'callback_url must be an http(s) url')
    return callback_url


def return_url(charge):
    """Where the buyer goes after paying: the shop's callback_url, carrying
    the shop's own reference so it knows which order to look up.

    Informational only. The shop must still verify with GET /charges/<ref>:
    a buyer can type this URL without paying.
    """
    if not charge.callback_url:
        return None

    parts = urlsplit(charge.callback_url)
    extra = urlencode({'reference': charge.reference,
                       'charge_code': charge.charge_code})
    query = f'{parts.query}&{extra}' if parts.query else extra
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query,
                       parts.fragment))


def merchant_bank_account(merchant):
    """The BellBank account a buyer transfers to, or None if not provisioned.

    This is the merchant owner's own virtual account. A merchant whose KYC has
    not produced one cannot be paid by transfer, and the checkout must say so
    rather than show nothing.
    """
    return VirtualAccountNumberModel.query.filter_by(
        user_id=merchant.user_id, is_active=True).first()


def _wallet_for(user_id, currency_id):
    return WalletModel.query.filter_by(
        user_id=user_id, currency_id=currency_id).first()


def pay_charge_from_wallet(charge, buyer, transaction_pin):
    """Settle `charge` by moving money between two Payverve wallets.

    Stages the debit, the credit, the transfer record and both transaction
    rows, and marks the charge paid. Does not commit: the caller wraps the
    whole settlement in one transaction so a failure cannot leave the buyer
    debited and the charge unpaid.
    """
    if charge.status == PAID:
        # Paying twice is a double charge, and the second attempt is usually a
        # retry of a request whose response was lost.
        raise RegistrationError(409, 'conflict',
                                'this charge has already been paid')

    if charge.is_expired():
        raise RegistrationError(410, 'gone',
                                'this payment window has closed, please '
                                'start a new checkout')

    if not buyer.transaction_pin:
        raise RegistrationError(400, 'bad request',
                                'set a transaction pin before paying')

    if not buyer.check_transaction_pin(transaction_pin):
        raise RegistrationError(400, 'bad request', 'incorrect transaction pin')

    merchant = MerchantModel.query.filter_by(id=charge.merchant_id).first()

    if not merchant or not merchant.is_active:
        raise RegistrationError(404, 'not found', 'merchant not found')

    if str(merchant.user_id) == str(buyer.id):
        raise RegistrationError(400, 'bad request',
                                'you cannot pay your own charge')

    buyer_wallet = WalletModel.query.filter_by(
        user_id=buyer.id, currency_ticker=charge.currency_ticker).first()

    if not buyer_wallet:
        raise RegistrationError(
            404, 'not found',
            f'you have no {charge.currency_ticker.upper()} wallet')

    merchant_wallet = _wallet_for(merchant.user_id, buyer_wallet.currency_id)

    if not merchant_wallet:
        raise RegistrationError(404, 'not found',
                                'this merchant cannot be paid in that currency')

    amount = float(charge.amount)
    buyer_balance = float(Cryptographer.decrypt(buyer_wallet.fund))

    if buyer_balance < amount:
        raise RegistrationError(400, 'bad request', 'insufficient funds')

    merchant_balance = float(Cryptographer.decrypt(merchant_wallet.fund))

    buyer_wallet.fund = Cryptographer.encrypt(str(buyer_balance - amount))
    merchant_wallet.fund = Cryptographer.encrypt(str(merchant_balance + amount))

    reference = f'PVC-{secrets.token_hex(8).upper()}'
    buyer_name = f'{buyer.first_name} {buyer.last_name}'
    narration = f'Payment to {merchant.business_name} ({charge.reference})'

    buyer_account = VirtualAccountNumberModel.query.filter_by(
        user_id=buyer.id, currency_id=buyer_wallet.currency_id).first()
    merchant_account = merchant_bank_account(merchant)

    # noinspection PyArgumentList
    transfer = PayverveTransferModel(
        amount=Cryptographer.encrypt(str(amount)),
        charge_amount=0.0,
        sender_name=buyer_name,
        sender_account_number=int(buyer_account.account_number)
        if buyer_account else 0,
        narration=narration,
        recipient_name=merchant.business_name,
        recipient_account_number=int(merchant_account.account_number)
        if merchant_account else 0,
        reference=reference,
        session_id=secrets.token_urlsafe(16),
        stamp_duty=0.0,
        transfer_pair=f'{buyer_wallet.currency_ticker.lower()}-'
                      f'{merchant_wallet.currency_ticker.lower()}',
        transaction_status='successful',
        user_id=buyer.id,
        wallet_id=buyer_wallet.id,
    )

    # noinspection PyArgumentList
    debit = TransactionModel(
        amount=Cryptographer.encrypt(str(amount)),
        transaction_type='merchant_payment',
        user_id=buyer.id,
        currency_id=buyer_wallet.currency_id,
        note=narration,
        status='successful',
        name=merchant.business_name,
        transaction_flow='debit',
        transaction_title='Payment Sent',
        currency_ticker=buyer_wallet.currency_ticker.lower(),
    )

    # noinspection PyArgumentList
    credit = TransactionModel(
        amount=Cryptographer.encrypt(str(amount)),
        transaction_type='merchant_payment',
        user_id=merchant.user_id,
        currency_id=merchant_wallet.currency_id,
        note=narration,
        status='successful',
        name=buyer_name,
        transaction_flow='credit',
        transaction_title='Payment Received',
        currency_ticker=merchant_wallet.currency_ticker.lower(),
    )

    charge.status = PAID
    charge.method = PAID_BY_WALLET
    charge.paid_at = datetime.now()
    charge.settlement_reference = reference

    db.session.add_all([buyer_wallet, merchant_wallet, transfer, debit, credit,
                        charge])
    return charge


def expire_if_due(charge):
    """Mark a charge expired once its window has passed. Does not commit."""
    from ..models.charge import EXPIRED

    if charge.is_expired():
        charge.status = EXPIRED
        db.session.add(charge)

    return charge


def match_inbound_payment(wallet, amount_received, session_id):
    """Settle a merchant's pending charge from a bank transfer that just landed.

    Called from the BellBank collection handler once the credit has been
    staged, and stages the charge in the same transaction, so a deposit is
    never credited while the charge it paid stays pending.

    Matching is on the amount the buyer SENT, not the amount the wallet
    received: BellBank deducts its fee on the way in, so the credited figure
    is smaller than the price the shop quoted.

    Returns the charge it settled, or None.

    The shop is paid into one shared account, so the amount is the only signal
    the sender carries -- there is no reference to read. That has two
    consequences worth being honest about:

      * two unpaid charges for the same amount are indistinguishable. The
        oldest is settled first, which is right when both buyers eventually
        pay and wrong, for one of them, if only one does. It is logged.
      * a transfer matching no charge is left as an ordinary deposit. It is
        the customer's money either way; it simply settles nothing.

    A per-charge virtual account removes the ambiguity entirely and is the
    proper fix. VirtualAccountNumberModel.account_type already anticipates it:
    'static' is the shared account, and a dynamic one would be issued per
    charge.
    """
    from ..models.charge import PAID_BY_TRANSFER

    if wallet is None or not amount_received:
        return None

    merchant = MerchantModel.query.filter_by(
        user_id=wallet.user_id, is_active=True).first()

    if not merchant:
        return None

    try:
        sent = Decimal(str(amount_received)).quantize(Decimal('0.01'))
    except Exception:
        return None

    # One transfer settles one charge. The webhook already rejects a repeated
    # sessionId before reaching here, but this must not depend on an upstream
    # caller to be safe: without the check, a replayed notification would
    # settle a second charge and the shop would ship two orders for one
    # payment.
    if session_id and ChargeModel.query.filter_by(
            settlement_reference=session_id).first():
        print(f'[checkout] session {session_id} already settled a charge; '
              f'ignoring')
        return None

    now = datetime.now()
    candidates = ChargeModel.query.filter(
        ChargeModel.merchant_id == merchant.id,
        ChargeModel.status == PENDING,
        ChargeModel.amount == sent,
        ChargeModel.expires_at > now,
    ).order_by(ChargeModel.created_at.asc()).all()

    if not candidates:
        return None

    if len(candidates) > 1:
        print(f'[checkout] {len(candidates)} open charges on merchant '
              f'{merchant.id} for {sent}; settling the oldest '
              f'({candidates[0].reference}) against session {session_id}. '
              f'A per-charge account would remove this ambiguity.')

    charge = candidates[0]
    charge.status = PAID
    charge.method = PAID_BY_TRANSFER
    charge.paid_at = now
    charge.settlement_reference = session_id
    db.session.add(charge)

    # Queued in this same transaction, alongside the credit that settled the
    # charge. Sending is the caller's job, after the commit: a shop's server
    # must never be in the path of crediting a customer's deposit.
    from .merchant_webhook import enqueue_charge_paid
    enqueue_charge_paid(charge, merchant)

    print(f'[checkout] charge {charge.reference} for merchant '
          f'{merchant.business_name} settled by transfer, session '
          f'{session_id}')
    return charge
