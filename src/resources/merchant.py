"""
src/resources/merchant.py

Registering a shop and issuing its keys.
"""
from flask import jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..models import MerchantModel, UserModel, db
from ..services import checkout
from ..services.registration import RegistrationError


class MerchantResource(Resource):
    """ A shop accepting payment through Payverve """

    @staticmethod
    def create():
        """Register the signed-in user's shop and issue its keys."""
        try:
            user_id = request.current_user['sub']
            user = UserModel.query.filter_by(id=user_id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no user account was found'
                }), 404

            payload = request.get_json(silent=True) or {}
            merchant, secret_key = checkout.stage_merchant(
                user, payload.get('business_name'))
            db.session.commit()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'merchant profile created',
                'data': {
                    'merchant_id': str(merchant.id),
                    'business_name': merchant.business_name,
                    'public_key': merchant.public_key,
                    # The only time this is ever returned. It is stored as a
                    # keyed hash, so Payverve cannot show it again -- which is
                    # the point, and the merchant must be told so plainly.
                    'secret_key': secret_key,
                    'notice': 'store the secret key now; it cannot be shown '
                              'again'
                }
            }), 201

        except RegistrationError as e:
            db.session.rollback()
            return jsonify(e.as_payload()), e.code

        except IntegrityError:
            db.session.rollback()
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'a merchant profile already exists'
            }), 409

        except DataError:
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except (InternalError, OperationalError, DisconnectionError,
                ProgrammingError, SQLAlchemyError):
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not create the merchant profile'
            }), 500

    @staticmethod
    def read_mine():
        """The signed-in user's shop. Never includes the secret key."""
        try:
            user_id = request.current_user['sub']
            merchant = MerchantModel.query.filter_by(
                user_id=user_id, is_active=True).first()

            if not merchant:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no merchant profile for this account'
                }), 404

            bank_account = checkout.merchant_bank_account(merchant)

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': {
                    'merchant_id': str(merchant.id),
                    'business_name': merchant.business_name,
                    'public_key': merchant.public_key,
                    'secret_key_preview': f'...{merchant.secret_key_preview}',
                    'is_active': merchant.is_active,
                    # Null until the owner's KYC produces a BellBank account.
                    # Without it the shop cannot be paid by bank transfer, and
                    # the checkout has to say so rather than show nothing.
                    'settlement_account_number':
                        bank_account.account_number if bank_account else None,
                    'settlement_bank':
                        bank_account.account_bank_name if bank_account else None,
                }
            }), 200

        except (InternalError, OperationalError, DisconnectionError,
                ProgrammingError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not fetch the merchant profile'
            }), 500
