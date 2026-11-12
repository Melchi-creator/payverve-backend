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
            merchant, secret_key, webhook_secret = checkout.stage_merchant(
                user, payload.get('business_name'),
                webhook_url=payload.get('webhook_url'))
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
                    'webhook_url': merchant.webhook_url,
                    # Used to verify the signature on webhooks we send. Like
                    # the secret key, shown once.
                    'webhook_secret': webhook_secret,
                    'notice': 'store the secret key and webhook secret now; '
                              'neither can be shown again'
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
                    'webhook_url': merchant.webhook_url,
                    'webhook_configured': bool(merchant.webhook_url
                                               and merchant.webhook_secret),
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


_DB_ERRORS = (InternalError, OperationalError, DisconnectionError,
              ProgrammingError, SQLAlchemyError)


def _owner_and_merchant():
    """The signed-in user and their active shop, or a 404 response."""
    user_id = request.current_user['sub']
    user = UserModel.query.filter_by(id=user_id).first()
    merchant = MerchantModel.query.filter_by(
        user_id=user_id, is_active=True).first() if user else None

    if not merchant:
        return None, None, (jsonify({
            'code': 404,
            'status_message': 'not found',
            'message': 'no merchant profile for this account'
        }), 404)
    return user, merchant, None


def _owner_change(action, success_message, failure_message):
    """Run one pin-protected change to the owner's shop in one transaction.

    `action(merchant, user, payload)` stages the change and returns the
    response data. Every refusal rolls back, so a wrong pin changes nothing.
    """
    try:
        user, merchant, refused = _owner_and_merchant()

        if refused:
            return refused

        payload = request.get_json(silent=True) or {}
        data = action(merchant, user, payload)
        db.session.commit()

        return jsonify({
            'code': 200,
            'status_message': 'success',
            'message': success_message,
            'data': data,
        }), 200

    except RegistrationError as e:
        db.session.rollback()
        return jsonify(e.as_payload()), e.code

    except _DB_ERRORS:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'status_message': 'database error',
            'message': failure_message
        }), 500


class MerchantSettingsResource(Resource):
    """ Keys and webhook settings of the signed-in owner's shop """

    @staticmethod
    def rotate_secret_key():
        """Issue a new secret key; the old one stops working at once."""
        def action(merchant, user, payload):
            secret_key = checkout.rotate_secret_key(
                merchant, user, payload.get('transaction_pin'))
            return {
                'public_key': merchant.public_key,
                'secret_key': secret_key,
                'notice': 'the previous secret key no longer works; update '
                          'your server now and store this key, it cannot '
                          'be shown again',
            }

        return _owner_change(action, 'secret key replaced',
                             'could not replace the secret key')

    @staticmethod
    def rotate_webhook_secret():
        """Issue a new webhook signing secret."""
        def action(merchant, user, payload):
            webhook_secret = checkout.rotate_webhook_secret(
                merchant, user, payload.get('transaction_pin'))
            return {
                'webhook_secret': webhook_secret,
                'notice': 'webhooks are now signed with this secret, '
                          'including retries already queued; store it, it '
                          'cannot be shown again',
            }

        return _owner_change(action, 'webhook secret replaced',
                             'could not replace the webhook secret')

    @staticmethod
    def update_webhook_url():
        """Change where payment events are posted, or turn them off (null)."""
        def action(merchant, user, payload):
            if 'webhook_url' not in payload:
                raise RegistrationError(
                    400, 'bad request',
                    'webhook_url is required (null turns webhooks off)')

            issued = checkout.update_webhook_url(
                merchant, user, payload.get('transaction_pin'),
                payload.get('webhook_url'))
            data = {
                'webhook_url': merchant.webhook_url,
                'webhook_configured': bool(merchant.webhook_url
                                           and merchant.webhook_secret),
            }

            if issued:
                data['webhook_secret'] = issued
                data['notice'] = 'store the webhook secret now; it cannot '                                  'be shown again'
            return data

        return _owner_change(action, 'webhook url updated',
                             'could not update the webhook url')
