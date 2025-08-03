"""

"""
from datetime import datetime, timedelta

from flask import jsonify
from flask_restful.reqparse import Argument
from psycopg2 import DataError, InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DBAPIError, DisconnectionError

import config
from ..models import AdminModel, UserModel
from ..utilities import encode_token, parse_params
from ..value_object import EmailCheck


class Authentication:
    """ """


    @staticmethod
    @parse_params(
        Argument("email_address", location="json", required=True),
        Argument("password", location="json", required=True),
    )
    def user_authentication(email_address: str, password: str):
        """ """

        try:

            EmailCheck(email_address)

            check_user = UserModel.query.filter_by(email_address=email_address).first()

            if not check_user:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'user not found'
                }), 404

            if not check_user.email_verified:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'data': 'email not verified'
                }), 403

            if not check_user.check_password(password):
                return jsonify({
                    'code': 401,
                    'code_message': 'unauthorized',
                    'data': 'invalid password'
                }), 401

            extra_payload = {
                'sub': str(check_user.id),
                'given_name': check_user.first_name,
                'family_name': check_user.last_name,
            }

            access_token = encode_token(extra_payload, config.access_token_time, config.access_secret_key)
            refresh_token = encode_token(extra_payload, config.refresh_token_time, config.refresh_secret_key)

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires': (datetime.now() + timedelta(seconds=config.access_token_time)).strftime('%I:%M %p'),
                    'refresh_token_expires': (
                            datetime.now() + timedelta(seconds=config.refresh_token_time)).strftime(
                        '%B %d, %Y at %I:%M %p'),
                    'id': str(check_user.id),
                    'message': f'{check_user.first_name} logged in successfully'
                }
            })

        except DataError:
            return jsonify({
                "code": 400,
                'code_message': 'bad request',
                "data": "this error is a datatype error",
            }), 400

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "data": "this error is a database error",
            }), 500

    @staticmethod
    @parse_params(
        Argument("email_address", location="json", required=True),
        Argument("password", location="json", required=True),
    )
    def admin_authentication(email_address: str, password: str):
        """ """

        try:

            EmailCheck(email_address)

            check_admin = AdminModel.query.filter_by(email_address=email_address).first()

            if not check_admin:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'user not found'
                }), 404

            if not check_admin.email_verified:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'data': 'email not verified'
                }), 403

            if not check_admin.check_password(password):
                return jsonify({
                    'code': 401,
                    'code_message': 'unauthorized',
                    'data': 'invalid password'
                }), 401

            extra_payload = {
                'sub': str(check_admin.id),
                'given_name': check_admin.first_name,
                'family_name': check_admin.last_name,
            }

            access_token = encode_token(extra_payload, config.access_token_time, config.access_secret_key)
            refresh_token = encode_token(extra_payload, config.refresh_token_time, config.refresh_secret_key)

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires': (datetime.now() + timedelta(seconds=config.access_token_time)).strftime('%I:%M %p'),
                    'refresh_token_expires': (
                            datetime.now() + timedelta(seconds=config.refresh_token_time)).strftime(
                        '%B %d, %Y at %I:%M %p'),
                    'id': str(check_admin.id),
                    'message': f'{check_admin.first_name} logged in successfully'
                }
            })

        except DataError:
            return jsonify({
                "code": 400,
                'code_message': 'bad request',
                "data": "this error is a datatype error",
            }), 400

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "data": "this error is a database error",
            }), 500