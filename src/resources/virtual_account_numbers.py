"""

"""
from datetime import datetime
from hmac import compare_digest

from flask import jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import DisconnectionError, \
    InternalError, \
    OperationalError, \
    ProgrammingError

from ..models import CurrencyModel, VirtualAccountNumberModel
from ..services import registration, virtual_account


class VirtualAccountNumberResource(Resource):
    """  """

    @staticmethod
    def read_all():
        """  """

        virtual_account_numbers = VirtualAccountNumberModel.query.all()

        try:
            if not virtual_account_numbers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no virtual accounts was found'
                }), 404

            data = [
                {
                    'id': virtual_account_number.id,
                    'virtual_account_id': virtual_account_number.virtual_account_id,
                    'account_number': virtual_account_number.account_number,
                    'reference': virtual_account_number.reference,
                    'bank_name': virtual_account_number.account_bank_name,
                    'account_type': virtual_account_number.account_type,
                    'status': virtual_account_number.status,
                    'expiry_date': virtual_account_number.account_expiration_datetime.strftime("%d %b %Y, %I:%M %p"),
                    'customer_code': virtual_account_number.customer_code,
                    'currency_ticker': virtual_account_number.currency_ticker,
                    'is_active': virtual_account_number.is_active,
                    'user_id': virtual_account_number.user_id,
                    'currency_id': virtual_account_number.currency_id,
                    'created_at': virtual_account_number.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': virtual_account_number.updated_at.strftime("%d %b %Y, %I:%M %p") if virtual_account_number.updated_at else None,
                }
                for virtual_account_number in virtual_account_numbers
            ]

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """  """

        virtual_account_number = VirtualAccountNumberModel.query.filter_by(
            id=id).first()

        try:
            if not virtual_account_number:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no virtual account was found'
                }), 404

            data = {
                'id': virtual_account_number.id,
                'virtual_account_id': virtual_account_number.virtual_account_id,
                'account_number': virtual_account_number.account_number,
                'reference': virtual_account_number.reference,
                'bank_name': virtual_account_number.account_bank_name,
                'account_type': virtual_account_number.account_type,
                'status': virtual_account_number.status,
                'expiry_date': virtual_account_number.account_expiration_datetime.strftime("%d %b %Y, %I:%M %p"),
                'customer_code': virtual_account_number.customer_code,
                'currency_ticker': virtual_account_number.currency_ticker,
                'is_active': virtual_account_number.is_active,
                'user_id': virtual_account_number.user_id,
                'currency_id': virtual_account_number.currency_id,
                'created_at': virtual_account_number.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': virtual_account_number.updated_at.strftime("%d %b %Y, %I:%M %p") if virtual_account_number.updated_at else None,
            }

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def user_virtual_account(id=None):
        """  """

        virtual_account_numbers = VirtualAccountNumberModel.query.filter_by(
            user_id=id).all()

        try:
            if not virtual_account_numbers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no virtual accounts was found'
                }), 404

            data = [
                {
                    'id': virtual_account_number.id,
                    'virtual_account_id': virtual_account_number.virtual_account_id,
                    'account_number': virtual_account_number.account_number,
                    'reference': virtual_account_number.reference,
                    'bank_name': virtual_account_number.account_bank_name,
                    'account_type': virtual_account_number.account_type,
                    'status': virtual_account_number.status,
                    'expiry_date': virtual_account_number.account_expiration_datetime.strftime("%d %b %Y, %I:%M %p"),
                    'customer_code': virtual_account_number.customer_code,
                    'currency_ticker': virtual_account_number.currency_ticker,
                    'is_active': virtual_account_number.is_active,
                    'user_id': virtual_account_number.user_id,
                    'currency_id': virtual_account_number.currency_id,
                    'created_at': virtual_account_number.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': virtual_account_number.updated_at.strftime("%d %b %Y, %I:%M %p") if virtual_account_number.updated_at else None,
                }
                for virtual_account_number in virtual_account_numbers
            ]

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as ve:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - value error',
                'message': str(ve)
            }), 400

    @staticmethod
    def user_one_virtual_account(id=None):
        """  """

        tickers = CurrencyModel.query.all()
        ticker = [t.short_code for t in tickers]
        currency_ticker = request.args.get('short-code')

        if not currency_ticker:
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'currency ticker is required'
            }), 400

        currency_ticker_lower = currency_ticker.lower()

        if currency_ticker_lower not in ticker:
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'ticker not available'
            }), 400

        currency_ticker = currency_ticker_lower.upper()

        virtual_account_number = VirtualAccountNumberModel.query.filter_by(
            user_id=id, currency_ticker=currency_ticker).first()

        try:
            if not virtual_account_number:

                # This branch used to create the account at Flutterwave, a
                # different provider from the one that owns NGN deposits, and
                # only ever ran because BellBank provisioning had not happened
                # for this user. Issuing a Flutterwave number here handed the
                # customer an account no BellBank webhook would ever credit.
                # Provision the right provider instead.
                if not compare_digest(currency_ticker, 'NGN'):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden',
                        'message': 'only ngn account numbers are available '
                                   'at the moment'
                    }), 403

                try:
                    virtual_account_number = (
                        virtual_account.ensure_ngn_virtual_account(id))
                except registration.RegistrationError as e:
                    return jsonify(e.as_payload()), e.code

                if not virtual_account_number:
                    return jsonify({
                        'code': 502,
                        'status_message': 'bad gateway',
                        'message': 'your account number could not be created, '
                                   'please try again later'
                    }), 502

            data = {
                'id': virtual_account_number.id,
                'virtual_account_id': virtual_account_number.virtual_account_id,
                'account_number': virtual_account_number.account_number,
                'reference': virtual_account_number.reference,
                'bank_name': virtual_account_number.account_bank_name,
                'account_type': virtual_account_number.account_type,
                'status': virtual_account_number.status,
                'expiry_date': virtual_account_number.account_expiration_datetime.strftime("%d %b %Y, %I:%M %p"),
                'customer_code': virtual_account_number.customer_code,
                'currency_ticker': virtual_account_number.currency_ticker,
                'is_active': virtual_account_number.is_active,
                'user_id': virtual_account_number.user_id,
                'currency_id': virtual_account_number.currency_id,
                'created_at': virtual_account_number.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': virtual_account_number.updated_at.strftime("%d %b %Y, %I:%M %p") if virtual_account_number.updated_at else None,
            }

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as ve:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - value error',
                'message': str(ve)
            }), 400
