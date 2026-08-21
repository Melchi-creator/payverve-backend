"""Provisioning real BellBank virtual accounts for NGN wallets.

Wallets used to be created with RandomGenerator.sim_account_number(), a made-up
ten-digit number. Nothing routed to it: the collection webhook resolves a
deposit with WalletModel.query.filter_by(account_number=...), so every real
BellBank notification failed to find a wallet and was ignored. Worse, the number
was shown to the customer as theirs, and at a real bank it may well belong to
somebody else.

BellBank issues an account against a verified identity, so provisioning needs a
BVN and an address -- which is a CBN requirement, not a BellBank quirk. A wallet
therefore starts with no account number and is provisioned once those are known,
either during registration when the client sends them or later from KYC.
"""
from datetime import datetime
from hmac import compare_digest

from ..models import VirtualAccountNumberModel, db
from .registration import RegistrationError

BELLBANK_BANK_NAME = 'bellbank microfinance bank'
TOKEN_VALIDITY_MINUTES = '5'


def _parse_expiry(value):
    """A static account has no expiry, so None is the normal case here."""
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue

    return None


def ensure_ngn_virtual_account(user_id):
    """Provision a user's NGN virtual account if it is still missing.

    Registration and wallet creation both provision, but only at that instant.
    A user whose KYC had no bvn or address at the time was left without an
    account, and nothing ever retried -- updating the KYC afterwards did not
    reach this code. That left the account permanently unprovisioned and sent
    the read endpoint down its legacy fallback instead.

    Returns the VirtualAccountNumberModel. Raises RegistrationError carrying
    the response the API should send when it cannot be provisioned yet.
    """
    # Imported here for the same reason provision_ngn_virtual_account defers
    # its BellbankHelper import: src.models is safe, but keeping both local
    # keeps this module importable from either side of the cycle.
    from ..models import CurrencyModel, KYCModel, UserModel, WalletModel

    currency = CurrencyModel.query.filter_by(short_code='ngn').first()

    if not currency:
        raise RegistrationError(
            404, 'not found', 'ngn currency is not configured')

    existing = VirtualAccountNumberModel.query.filter_by(
        user_id=user_id, currency_id=currency.id).first()

    if existing:
        return existing

    user = UserModel.query.filter_by(id=user_id).first()

    if not user:
        raise RegistrationError(
            404, 'not found', 'the customer was not found')

    kyc = KYCModel.query.filter_by(user_id=user_id).first()

    if not kyc:
        raise RegistrationError(
            409, 'unauthorise', 'complete your kyc before proceeding')

    wallet = WalletModel.query.filter_by(
        user_id=user_id, currency_id=currency.id).first()

    if not wallet:
        raise RegistrationError(
            404, 'not found', 'no ngn wallet to provision')

    try:
        provision_ngn_virtual_account(
            user, wallet, kyc.bvn, kyc.address, currency.id)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return VirtualAccountNumberModel.query.filter_by(
        user_id=user_id, currency_id=currency.id).first()


def provision_ngn_virtual_account(user, wallet, bvn, address, currency_id=None):
    """Attach a real BellBank virtual account to an NGN wallet.

    Stages the change in the session; the caller commits. Returns the wallet.
    Raises RegistrationError with the response the API should send.
    """
    if wallet is None:
        raise RegistrationError(
            404, 'not found', 'no ngn wallet to provision')

    # Already provisioned. BellBank keys the request on the customer's details
    # so a retry is safe, but there is no reason to make the call.
    existing = VirtualAccountNumberModel.query.filter_by(
        user_id=user.id, currency_id=currency_id or wallet.currency_id).first()

    if existing:
        return wallet

    if not bvn:
        raise RegistrationError(
            400, 'bad request',
            'a bvn is required to create your account number')

    if not address:
        raise RegistrationError(
            400, 'bad request',
            'an address is required to create your account number')

    # Imported here, not at module scope: src.middlewares imports
    # src.resources, which imports src.middlewares back, so pulling it in at
    # import time makes the cycle fail depending on which side loads first.
    from ..middlewares import BellbankHelper

    access_token = BellbankHelper.bellbank_authentication(
        TOKEN_VALIDITY_MINUTES)

    if not access_token:
        raise RegistrationError(
            502, 'bad gateway', 'could not authenticate with the bank')

    response = BellbankHelper.bellbank_virtual_account(
        access_token=access_token,
        mobile_number=user.mobile_number,
        first_name=user.first_name,
        last_name=user.last_name,
        address=str(address),
        bvn=bvn,
        gender=user.gender,
        date_of_birth=str(user.date_of_birth),
        meta_data={'email_address': user.email_address},
    )

    # The helper returns a jsonify tuple instead of a response when it catches,
    # so a plain status_code check is not enough to trust what came back.
    status_code = getattr(response, 'status_code', None)

    if status_code is None:
        raise RegistrationError(
            502, 'bad gateway', 'the bank did not return a usable response')

    if not compare_digest(str(status_code), '200'):
        try:
            message = response.json().get(
                'message', 'the bank rejected the account request')
        except ValueError:
            message = 'the bank returned an unexpected response'
        raise RegistrationError(status_code, 'bad gateway', message)

    try:
        data = response.json().get('data') or {}
    except ValueError:
        raise RegistrationError(
            502, 'bad gateway', 'the bank returned an unexpected response')

    account_number = data.get('accountNumber')

    if not account_number:
        raise RegistrationError(
            502, 'bad gateway', 'the bank did not return an account number')

    # Deposits are matched on this column, so a collision would send somebody
    # else's money here. Refuse rather than overwrite.
    clash = VirtualAccountNumberModel.query.filter_by(
        account_number=str(account_number)).first()

    if clash and str(clash.user_id) != str(user.id):
        raise RegistrationError(
            409, 'conflict',
            'that account number is already assigned to another user')

    external_reference = data.get('externalReference') or str(account_number)
    bank_name = data.get('bankName') or BELLBANK_BANK_NAME

    # Account details live here rather than on the wallet: migration
    # 2129b3c36f79 dropped those columns from wallets.
    # noinspection PyArgumentList
    db.session.add(VirtualAccountNumberModel(
        virtual_account_id=str(data.get('id') or external_reference),
        account_number=str(account_number),
        reference=external_reference,
        account_bank_name=bank_name,
        account_type='static',
        status='active',
        account_expiration_datetime=_parse_expiry(data.get('expiryDate')),
        customer_code=user.customer_code,
        currency_ticker='NGN',
        is_active=True,
        user_id=user.id,
        currency_id=currency_id or wallet.currency_id,
    ))

    wallet.is_active = True
    db.session.add(wallet)

    return wallet
