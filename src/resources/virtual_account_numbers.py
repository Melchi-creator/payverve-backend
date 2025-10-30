"""

"""
from flask import jsonify
from flask_restful import Resource
from sqlalchemy.exc import DisconnectionError, \
    InternalError, \
    OperationalError, \
    ProgrammingError

from ..models import VirtualAccountNumberModel


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
                    'response_status_message': virtual_account_number.response_status_message,
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
                    'created_at': virtual_account_number.created_at,
                    'updated_at': virtual_account_number.updated_at
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
                'response_status_message': virtual_account_number.response_status_message,
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
                'created_at': virtual_account_number.created_at,
                'updated_at': virtual_account_number.updated_at
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
                    'response_status_message': virtual_account_number.response_status_message,
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
                    'created_at': virtual_account_number.created_at,
                    'updated_at': virtual_account_number.updated_at
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
