"""
src/resources/payverve_wallet.py
This module defines the PayverveWalletResource class, which provides an API endpoint to retrieve all
Payverve wallet funds. It handles various exceptions that may occur during database operations
and returns appropriate JSON responses.
"""
from flask import jsonify
from flask_restful import Resource
from psycopg2 import InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DisconnectionError

from src.models import PayverveWalletModel
from src.utilities import Cryptographer


class PayverveWalletResource(Resource):
    """ Payverve Wallet Resource """

    @staticmethod
    def read():
        """ Retrieve  Payverve wallet funds"""

        try:
            payverve_funds = PayverveWalletModel.query.order_by(PayverveWalletModel.created_at.desc()).first()

            data = {
                "id": payverve_funds.id,
                "fund": Cryptographer.decrypt(payverve_funds.fund),
                "created_at": payverve_funds.created_at.isoformat(),
                "updated_at": payverve_funds.updated_at.isoformat() if payverve_funds.updated_at else None
            }

            return jsonify({
                "status": "success",
                "message": "Payverve funds retrieved successfully",
                "data": data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500
