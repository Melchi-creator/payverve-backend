"""Registration steps as directly callable units.

Registration used to drive itself over HTTP: the create-user handler POSTed to
its own /ngn-wallets, /referrals and /kycs endpoints. That put three network
hops inside one signup, forced those money-moving routes to be publicly
reachable, and -- because each hop committed independently -- made a failure
part-way through unrecoverable except by compensating deletes and claw-backs
that were themselves wrong on most paths.

These functions stage their work in the SQLAlchemy session and deliberately do
not commit, so one caller can wrap the whole signup in a single transaction and
let a rollback undo everything. Callers must commit.
"""
from ..models import (CurrencyModel, KYCModel, NotificationModel,
                      ReferralModel, WalletModel, db)
from ..utilities import Cryptographer
from ..value_object import MinimumBalance

REFERRAL_BONUS = float(500.00)


class RegistrationError(Exception):
    """A step refused to proceed, carrying the response the API should send."""

    def __init__(self, code, status_message, message):
        super().__init__(message)
        self.code = code
        self.status_message = status_message
        self.message = message

    def as_payload(self):
        return {
            'code': self.code,
            'status_message': self.status_message,
            'message': self.message,
        }


def ngn_currency_id():
    """Id of the naira currency, or raise if the table was never seeded."""
    currency = CurrencyModel.query.filter_by(short_code='ngn').first()

    if not currency:
        raise RegistrationError(
            500, 'internal server error', 'ngn currency is not configured')

    return currency.id


def stage_ngn_wallet(user_id, currency_id=None):
    """Stage an NGN wallet and its notification. Does not commit."""
    if currency_id is None:
        currency_id = ngn_currency_id()

    initial_fund = float(0)
    MinimumBalance(initial_fund)

    # Account details live on virtual_account_numbers, not here: migration
    # 2129b3c36f79 dropped account_number, bank_name and external_reference
    # from wallets. The number is attached by
    # virtual_account.provision_ngn_virtual_account once a bvn and address are
    # known. It is never given a placeholder -- deposits are matched on it.
    # noinspection PyArgumentList
    wallet = WalletModel(
        fund=Cryptographer.encrypt(initial_fund),
        user_id=user_id,
        currency_id=currency_id,
        currency_ticker='ngn',
        is_active=False,
    )

    # noinspection PyArgumentList
    notification = NotificationModel(
        title='Wallet Creation',
        body='Your NGN wallet has been created. Complete your verification to '
             'get your account number.',
        user_id=user_id,
    )

    db.session.add_all([wallet, notification])
    return wallet


def stage_referral(referrer, referred, currency_id=None):
    """Stage the referral and credit both wallets. Does not commit.

    Every guard runs before anything is written, so a refusal leaves no
    referral row and moves no money.
    """
    if str(referrer.id) == str(referred.id):
        raise RegistrationError(
            400, 'bad request', 'a user cannot refer themselves')

    # A user can only ever be referred once. There is no unique constraint on
    # referrals, so without this the bonus could be paid again on a replay.
    if ReferralModel.query.filter_by(referred_id=str(referred.id)).first():
        raise RegistrationError(
            409, 'conflict', 'this user has already been referred')

    if currency_id is None:
        currency_id = ngn_currency_id()

    referrer_wallet = WalletModel.query.filter_by(
        user_id=referrer.id, currency_id=currency_id).first()
    referred_wallet = WalletModel.query.filter_by(
        user_id=referred.id, currency_id=currency_id).first()

    if not referrer_wallet or not referred_wallet:
        raise RegistrationError(
            404, 'not found',
            'an ngn wallet for the referral pair was not found')

    referrer_fund = float(Cryptographer.decrypt(referrer_wallet.fund))
    referred_fund = float(Cryptographer.decrypt(referred_wallet.fund))
    MinimumBalance(referrer_fund)
    MinimumBalance(referred_fund)

    referrer_wallet.fund = Cryptographer.encrypt(referrer_fund + REFERRAL_BONUS)
    referred_wallet.fund = Cryptographer.encrypt(referred_fund + REFERRAL_BONUS)

    # noinspection PyArgumentList
    referral = ReferralModel(
        referral_id=str(referrer.id),
        referral_code=referrer.user_code,
        referred_id=str(referred.id),
        referred_code=referred.user_code,
    )

    db.session.add_all([referral, referrer_wallet, referred_wallet])
    return referral


def stage_kyc(user_id, full_name, mobile_number):
    """Stage a starter KYC record. Does not commit."""
    if full_name is None:
        raise RegistrationError(
            400, 'bad request', 'full name is required to create kyc')

    if mobile_number is None:
        raise RegistrationError(
            400, 'bad request', 'mobile number is required to create kyc')

    # noinspection PyArgumentList
    kyc = KYCModel(
        user_id=user_id,
        full_name_present=True,
        phone_number_present=True,
    )

    db.session.add(kyc)
    return kyc
