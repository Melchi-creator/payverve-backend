"""

"""
import secrets
from datetime import datetime
from hmac import compare_digest

from flask import jsonify
from flask_restful import Resource
from sqlalchemy.exc import DisconnectionError, \
    InternalError, \
    OperationalError, \
    ProgrammingError

from ..middlewares import FlutterwaveHelper
from ..models import CurrencyModel, KYCModel, UserModel, VirtualAccountNumberModel


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
                    'response_code': virtual_account_number.response_code,
                    'response_message': virtual_account_number.response_message,
                    'flw_ref': virtual_account_number.flw_ref,
                    'order_ref': virtual_account_number.order_ref,
                    'frequency': virtual_account_number.frequency,
                    'created_at_by_flw': virtual_account_number.created_at_by_flw,
                    'expiry_date': virtual_account_number.expiry_date,
                    'account_number': virtual_account_number.account_number,
                    'bank_name': virtual_account_number.bank_name,
                    'note': virtual_account_number.note,
                    'amount': virtual_account_number.amount,
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

        virtual_account_number = VirtualAccountNumberModel.query.filter_by(id=id).first()

        try:
            if not virtual_account_number:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no virtual account was found'
                }), 404

            data = {
                'id': virtual_account_number.id,
                'response_code': virtual_account_number.response_code,
                'response_message': virtual_account_number.response_message,
                'flw_ref': virtual_account_number.flw_ref,
                'order_ref': virtual_account_number.order_ref,
                'frequency': virtual_account_number.frequency,
                'created_at_by_flw': virtual_account_number.created_at_by_flw,
                'expiry_date': virtual_account_number.expiry_date,
                'account_number': virtual_account_number.account_number,
                'bank_name': virtual_account_number.bank_name,
                'note': virtual_account_number.note,
                'amount': virtual_account_number.amount,
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

        virtual_account_numbers = VirtualAccountNumberModel.query.filter_by(user_id=id).all()

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
                    'response_code': virtual_account_number.response_code,
                    'response_message': virtual_account_number.response_message,
                    'flw_ref': virtual_account_number.flw_ref,
                    'order_ref': virtual_account_number.order_ref,
                    'frequency': virtual_account_number.frequency,
                    'created_at_by_flw': virtual_account_number.created_at_by_flw,
                    'expiry_date': virtual_account_number.expiry_date,
                    'account_number': virtual_account_number.account_number,
                    'bank_name': virtual_account_number.bank_name,
                    'note': virtual_account_number.note,
                    'amount': virtual_account_number.amount,
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
    def user_one_virtual_account(id=None, currency_ticker=None):
        """  """

        ticker = [ticker.short_code for ticker in CurrencyModel]

        print('currency ticker: ', ticker)

        if currency_ticker not in ticker:
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'ticker not available'
            })

        virtual_account_number = VirtualAccountNumberModel.query.filter_by(user_id=id, currency_ticker=currency_ticker).first()

        try:
            if not virtual_account_number:

                kyc_check = KYCModel.query.filter_by(user_id=id).first()

                if not compare_digest(str(kyc_check.tier), '3'):
                    return jsonify({
                        'code': 409,
                        'status_message': 'unauthorise',
                        'message': 'complete your kyc before proceeding'
                    }), 409

                user_datails = UserModel.query.filter_by(id=id).first()
                reference_number = secrets.token_urlsafe(16)
                auth = FlutterwaveHelper.flutterwave_authentication()

                print('user_datails: ', user_datails)

                ## Flutterwave Virtual Account

                create_virtual_account = FlutterwaveHelper.virtual_account(auth,
                                                                           reference_number,
                                                                           user_datails.customer_code,
                                                                           user_datails.email_address)

                print('create_virtual_account: ', create_virtual_account)

                create_virtual_account_json = create_virtual_account.json().get('data')

                if compare_digest(str(create_virtual_account.status_code), '201'):
                    # noinspection PyArgumentList
                    create_bank_account = VirtualAccountNumberModel(
                        virtual_account_id=create_virtual_account_json.get('id'),
                        account_number=create_virtual_account_json.get('account_number'),
                        reference=reference_number,
                        account_bank_name=create_virtual_account_json.get('account_bank_name'),
                        account_type=create_virtual_account_json.get('account_type'),
                        account_expiration_datetime=datetime.strptime(create_virtual_account_json.get(
                            'account_expiration_datetime'),
                            "%Y-%m-%d %H:%M:%S"),
                        customer_code=user_datails.customer_code,
                    )
                    create_bank_account.save()

                if not compare_digest(str(create_virtual_account.status_code),
                                      '201') and not compare_digest(str(create_virtual_account.status_code), '409'):
                    return jsonify({
                        'code': create_virtual_account.status_code,
                        'status_message': create_virtual_account.get('status'),
                        'message': create_virtual_account_json.get('error').get('message')
                    }), create_virtual_account.status_code

                if compare_digest(str(create_virtual_account.status_code), '409'):
                    search_virtual_account = FlutterwaveHelper.retreive_virtual_account(auth,
                                                                                        create_virtual_account_json.get(
                                                                                            'id'))

                    search_virtual_account_json = search_virtual_account.json()

                    if not compare_digest(str(search_virtual_account.status_code), '200'):
                        return jsonify({
                            'code': search_virtual_account.status_code,
                            'status_message': search_virtual_account_json.get('status'),
                            'message': search_virtual_account_json.get('error').get('message')
                        }), create_virtual_account.status_code

                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no virtual accounts was found'
                }), 404

            data = {
                    'id': virtual_account_number.id,
                    'response_code': virtual_account_number.response_code,
                    'response_message': virtual_account_number.response_message,
                    'flw_ref': virtual_account_number.flw_ref,
                    'order_ref': virtual_account_number.order_ref,
                    'frequency': virtual_account_number.frequency,
                    'created_at_by_flw': virtual_account_number.created_at_by_flw,
                    'expiry_date': virtual_account_number.expiry_date,
                    'account_number': virtual_account_number.account_number,
                    'bank_name': virtual_account_number.bank_name,
                    'note': virtual_account_number.note,
                    'amount': virtual_account_number.amount,
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
