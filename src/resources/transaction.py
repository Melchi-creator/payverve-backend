"""

"""

from flask import jsonify
from flask_restful import Resource
from sqlalchemy.exc import DisconnectionError, \
    InternalError, \
    OperationalError, \
    ProgrammingError

from ..models import TransactionModel
from ..utilities import Cryptographer


class TransactionResource(Resource):
    """  """

    @staticmethod
    def read_all():
        """ """

        transactions = TransactionModel.query.order_by(TransactionModel.created_at.desc()).all()

        try:
            if not transactions:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no transactions was found'
                }), 404

            data = []

            for transaction in transactions:
                data.append({
                    'id': transaction.id,
                    'tx_ref': transaction.tx_ref,
                    'flw_ref': transaction.flw_ref,
                    'amount': Cryptographer.decrypt(transaction.amount),
                    'transaction_type': transaction.transaction_type,
                    'note': transaction.note,
                    'user_id': transaction.user_id,
                    'user': transaction.users.first_name + ' ' + transaction.users.last_name,
                    'currency_id': transaction.currency_id,
                    'created_at': transaction.created_at,
                    'updated_at': transaction.updated_at
                })

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'mesaage': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'mesaage': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'mesaage': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """ """

        transaction = TransactionModel.query.filter_by(id=id).first()

        try:
            if not transaction:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'transaction was not found'
                }), 404

            data = {
                'id': transaction.id,
                'tx_ref': transaction.tx_ref,
                'flw_ref': transaction.flw_ref,
                'amount': Cryptographer.decrypt(transaction.amount),
                'transaction_type': transaction.transaction_type,
                'note': transaction.note,
                'user_id': transaction.user_id,
                'user': transaction.users.first_name + ' ' + transaction.users.last_name,
                'currency_id': transaction.currency_id,
                'created_at': transaction.created_at,
                'updated_at': transaction.updated_at
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
    def user_transation(id=None):
        """ """

        transactions = TransactionModel.query.filter_by(user_id=id).all()

        try:
            if not transactions:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'transaction was not found for this user'
                }), 404

            data = []

            for transaction in transactions:
                data.append({
                    'id': transaction.id,
                    'tx_ref': transaction.tx_ref,
                    'flw_ref': transaction.flw_ref,
                    'amount': Cryptographer.decrypt(transaction.amount),
                    'transaction_type': transaction.transaction_type,
                    'note': transaction.note,
                    'user_id': transaction.user_id,
                    'user': transaction.users.first_name + ' ' + transaction.users.last_name,
                    'currency_id': transaction.currency_id,
                    'created_at': transaction.created_at,
                    'updated_at': transaction.updated_at
                })

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
                'mesaage': 'could not fetch table'
            }), 500
