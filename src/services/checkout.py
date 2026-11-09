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
import secrets
from datetime import datetime, timedelta
from decimal import Decimal

from ..models import (ChargeModel, MerchantModel, PayverveTransferModel,
                      TransactionModel, VirtualAccountNumberModel, WalletModel,
                      db)
from ..models.charge import (CHARGE_TTL_SECONDS, PAID, PAID_BY_WALLET,
                             PENDING)
from ..utilities import Cryptographer, hash_identifier
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


def stage_merchant(user, business_name):
    """Register a shop for `user`. Does not commit.

    Returns (merchant, secret_key) -- the only moment the secret exists.
    """
    name = (business_name or '').strip()

    if not name:
        raise RegistrationError(400, 'bad request',
                                'a business name is required')

    if MerchantModel.query.filter_by(user_id=user.id, is_active=True).first():
        raise RegistrationError(409, 'conflict',
                                'this account already has a merchant profile')

    public_key, secret_key, secret_hash, preview = issue_keys()

    # noinspection PyArgumentList
    merchant = MerchantModel(
        business_name=name,
        public_key=public_key,
        secret_key_hash=secret_hash,
        secret_key_preview=preview,
        user_id=user.id,
    )
    db.session.add(merchant)
    return merchant, secret_key


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
