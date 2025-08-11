"""
src/resources/token_verification.py
This module contains the TokenVerificationRepository class, which is used to interact with the TokenVerificationModel
"""
from flask import jsonify
from psycopg2 import InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DBAPIError, DisconnectionError

from ..models.token_verification import TokenVerificationModel


class TokenVerificationRepository:
    """ this class is used to interact with the TokenVerificationModel """

    @staticmethod
    def read():
        """ this method is used to get all the token verifications """

        try:

            token_verifications = TokenVerificationModel.query.all()

            if not token_verifications:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'no token found'
                }), 404

            data = [
                {
                    'id': token_verification.id,
                    'channel': token_verification.channel,
                    'channel_contact': token_verification.channel_contact,
                    'code_sent': token_verification.code_sent,
                    'expiration_time': token_verification.expiration_time,
                    'timestamp': token_verification.timestamp,
                    'status': token_verification.status,
                    'created_at': token_verification.created_at,
                    'updated_at': token_verification.updated_at
                }
                for token_verification in token_verifications
            ]

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': data
            }), 200

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "data": "this error is a database error",
            }), 500
