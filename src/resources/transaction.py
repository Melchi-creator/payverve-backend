"""

"""

from flask import jsonify
from flask_restful import Resource
from sqlalchemy.exc import DisconnectionError, \
    InternalError, \
    OperationalError, \
    ProgrammingError

from ..auth import (caller_id, caller_is_admin, not_found, owns)
from ..models import TransactionModel
from ..utilities import Cryptographer


class TransactionResource(Resource):
    """  """

    @staticmethod
    def read_all():
        """ """

        transactions = TransactionModel.query.order_by(TransactionModel.created_at.desc()).all()
        # Was an unscoped dump of every row to any signed-in customer.
        # Filtered on the result rather than in the query so the existing
        # ordering and shape are untouched; these tables are small.
        if not caller_is_admin():
            _me = caller_id()
            transactions = [r for r in transactions
                      if str(getattr(r, 'user_id', None)) == _me]


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
                    'tx_originator_name': transaction.users.first_name + ' ' + transaction.users.last_name,
                    'currency_id': transaction.currency_id,
                    'name': transaction.name,
                    'transaction_flow': transaction.transaction_flow,
                    'transaction_title': transaction.transaction_title,
                    'currency_ticker': transaction.currency_ticker,
                    'created_at': transaction.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': transaction.updated_at.strftime("%d %b %Y, %I:%M %p") if transaction.updated_at else None,
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
            # the id in the path was trusted outright, with no check that it belongs to the caller.
            _owner = TransactionModel.query.filter_by(id=id).first()
            if _owner is not None and not owns(_owner.user_id):
                return not_found(
                    'no transaction was found')

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
                'tx_originator_name': transaction.users.first_name + ' ' + transaction.users.last_name,
                'currency_id': transaction.currency_id,
                'name': transaction.name,
                'transaction_flow': transaction.transaction_flow,
                'transaction_title': transaction.transaction_title,
                'currency_ticker': transaction.currency_ticker,
                'created_at': transaction.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': transaction.updated_at.strftime("%d %b %Y, %I:%M %p") if transaction.updated_at else None,
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
            # the id in the path was trusted outright, with no check that it belongs to the caller.
            if not owns(id):
                return not_found(
                    'no transaction was found')

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
                    'tx_originator_name': transaction.users.first_name + ' ' + transaction.users.last_name,
                    'currency_id': transaction.currency_id,
                    'name': transaction.name,
                    'transaction_flow': transaction.transaction_flow,
                    'transaction_title': transaction.transaction_title,
                    'currency_ticker': transaction.currency_ticker,
                    'created_at': transaction.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': transaction.updated_at.strftime("%d %b %Y, %I:%M %p") if transaction.updated_at else None,
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
