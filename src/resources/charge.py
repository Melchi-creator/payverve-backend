"""
src/resources/charge.py

Creating a charge, showing it to a buyer, and settling it.

Three audiences, three authentications:

  the shop's server   secret key    creates and verifies charges
  the buyer's browser charge_code   reads what to pay and how, no session
  the buyer in-app    jwt           pays from their Payverve wallet

The checkout read is deliberately unauthenticated: a buyer following a link
from a shop has no Payverve session yet. It therefore returns only what is
needed to pay -- amount, shop name, where to send money, how long is left --
and nothing about the shop's other charges or the buyer.
"""
from flask import jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..models import ChargeModel, MerchantModel, UserModel, db
from ..services import checkout
from ..services.registration import RegistrationError

DATABASE_ERRORS = (InternalError, OperationalError, DisconnectionError,
                   ProgrammingError, SQLAlchemyError)


def _charge_view(charge, merchant, include_payment_details):
    """What a buyer is shown. Never the shop's keys or other charges."""
    view = {
        'charge_code': charge.charge_code,
        'reference': charge.reference,
        'amount': f'{charge.amount:.2f}',
        'currency': charge.currency_ticker.upper(),
        'status': charge.status,
        'method': charge.method,
        'business_name': merchant.business_name,
        'expires_at': charge.expires_at.isoformat(),
        # Drives the countdown on the checkout screen.
        'seconds_remaining': charge.seconds_remaining(),
    }

    if include_payment_details:
        bank_account = checkout.merchant_bank_account(merchant)
        view['bank_transfer'] = {
            'available': bank_account is not None,
            'account_number':
                bank_account.account_number if bank_account else None,
            'bank_name':
                bank_account.account_bank_name if bank_account else None,
            'account_name': merchant.business_name,
            # Said plainly, because a shop whose owner has not finished KYC
            # has no account to be paid into and the buyer must not be left
            # staring at a blank field.
            'unavailable_reason': None if bank_account else
                'this shop cannot accept bank transfers yet',
        }
        view['wallet'] = {
            'available': True,
            'description': 'pay instantly from your Payverve balance',
        }

    return view


class ChargeResource(Resource):
    """ One intended payment to a merchant """

    @staticmethod
    def create(merchant=None):
        """Shop server creates a charge. Idempotent on its own reference."""
        try:
            payload = request.get_json(silent=True) or {}
            charge = checkout.stage_charge(
                merchant,
                reference=payload.get('reference'),
                amount=payload.get('amount'),
                callback_url=payload.get('callback_url'),
                currency_ticker=payload.get('currency', 'ngn'),
            )
            db.session.commit()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'data': {
                    **_charge_view(charge, merchant, False),
                    'checkout_url': f'/checkout/{charge.charge_code}',
                }
            }), 201

        except RegistrationError as e:
            db.session.rollback()
            return jsonify(e.as_payload()), e.code

        except (IntegrityError, DataError):
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'ensure input data are correct'
            }), 400

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not create the charge'
            }), 500

    @staticmethod
    def verify(reference=None, merchant=None):
        """Shop server asks whether its own reference is paid.

        This is the only answer a shop should act on. The buyer being
        redirected back proves nothing: that redirect is under their control.
        """
        try:
            charge = ChargeModel.query.filter_by(
                merchant_id=merchant.id, reference=reference).first()

            if not charge:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no charge with that reference'
                }), 404

            checkout.expire_if_due(charge)
            db.session.commit()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': {
                    **_charge_view(charge, merchant, False),
                    'paid': charge.status == 'paid',
                    'paid_at': charge.paid_at.isoformat()
                    if charge.paid_at else None,
                    'settlement_reference': charge.settlement_reference,
                }
            }), 200

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not fetch the charge'
            }), 500


class CheckoutResource(Resource):
    """ What a buyer sees and does """

    @staticmethod
    def read(charge_code=None):
        """What to pay, to whom, how, and how long is left. No session needed."""
        try:
            charge = ChargeModel.query.filter_by(
                charge_code=charge_code).first()

            if not charge:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'this checkout link is not valid'
                }), 404

            merchant = MerchantModel.query.filter_by(
                id=charge.merchant_id).first()

            checkout.expire_if_due(charge)
            db.session.commit()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': _charge_view(charge, merchant, True)
            }), 200

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not load the checkout'
            }), 500

    @staticmethod
    def pay_with_wallet(charge_code=None):
        """Buyer settles the charge from their Payverve balance."""
        try:
            buyer_id = request.current_user['sub']
            buyer = UserModel.query.filter_by(id=buyer_id).first()

            if not buyer:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no user account was found'
                }), 404

            charge = ChargeModel.query.filter_by(
                charge_code=charge_code).first()

            if not charge:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'this checkout link is not valid'
                }), 404

            payload = request.get_json(silent=True) or {}

            # One transaction: the debit, the credit and the charge becoming
            # paid land together or not at all.
            checkout.pay_charge_from_wallet(
                charge, buyer, payload.get('transaction_pin'))
            db.session.commit()

            merchant = MerchantModel.query.filter_by(
                id=charge.merchant_id).first()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'payment successful',
                'data': {
                    **_charge_view(charge, merchant, False),
                    'paid': True,
                    'settlement_reference': charge.settlement_reference,
                    'callback_url': charge.callback_url,
                }
            }), 200

        except RegistrationError as e:
            db.session.rollback()
            return jsonify(e.as_payload()), e.code

        except (IntegrityError, DataError):
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'ensure input data are correct'
            }), 400

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'the payment could not be completed'
            }), 500
