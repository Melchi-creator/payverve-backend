"""

"""
import secrets
from datetime import datetime, timedelta

from flask import jsonify, make_response, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from psycopg2 import DataError, InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DBAPIError, DisconnectionError

import config
from src.models import AdminModel, UserModel
from src.utilities import Cryptographer, decode_token, encode_token, parse_params
from src.value_object import EmailCheck


class Authentication(Resource):
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
                    'message': 'user not found'
                }), 404

            # if not check_user.email_verified:
            #     return jsonify({
            #         'code': 403,
            #         'code_message': 'forbidden',
            #         'message': 'email not verified'
            #     }), 403
            # 
            # if not check_user.account_active:
            #     return jsonify({
            #         'code': 403,
            #         'code_message': 'forbidden',
            #         'message': 'user account is inactive, contact admin'
            #     }), 403

            if check_user.deleted:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': 'user account has been deleted, contact admin'
                }), 403

            if not check_user.check_password(password):
                return jsonify({
                    'code': 401,
                    'code_message': 'unauthorized',
                    'message': 'invalid password'
                }), 401

            extra_payload = {
                'sub': str(check_user.id),
                'given_name': check_user.first_name,
                'family_name': check_user.last_name,
            }

            jti = secrets.token_urlsafe(16)

            access_token = encode_token(extra_payload, jti, config.access_token_time, config.access_secret_key)
            refresh_token = encode_token(extra_payload, jti, config.refresh_token_time, config.refresh_secret_key)

            # Build response body
            response_body = {
                'code': 200,
                'code_message': 'successful',
                'message': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires': (datetime.now() + timedelta(seconds=config.access_token_time)).strftime('%I:%M %p'),
                    'refresh_token_expires': (
                            datetime.now() + timedelta(seconds=config.refresh_token_time)).strftime(
                        '%B %d, %Y at %I:%M %p'),
                    'id': str(check_user.id),
                    'message': f'{check_user.first_name} logged in successfully',
                    'email_verified': check_user.email_verified,
                    'account_active': check_user.account_active,
                    'account_deleted': check_user.deleted
                }
            }

            # Create a response object
            response = make_response(jsonify(response_body))

            # Set secure HTTP-only cookie for access token
            response.set_cookie(
                'access_token', access_token,
                httponly=False if config.debug is True else True,
                secure=False if config.debug is True else True,  # Only over HTTPS
                samesite='None',  # Prevent CSRF
                max_age=config.access_token_time
            )

            # Set secure HTTP-only cookie for refresh token
            response.set_cookie(
                'refresh_token', refresh_token,
                httponly=False if config.debug is True else True,
                secure=False if config.debug is True else True,
                samesite='None',
                max_age=config.refresh_token_time
            )

            check_user.jti = Cryptographer.encrypt(jti)
            check_user.save()

            return response

        except DataError:
            return jsonify({
                "code": 400,
                'code_message': 'bad request',
                "message": "this error is a datatype error",
            }), 400

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "message": "this error is a database error",
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
                    'message': 'user not found'
                }), 404

            if not check_admin.email_verified:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': 'email not verified'
                }), 403

            if not check_admin.account_active:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': 'admin account is inactive, contact super admin'
                }), 403

            if check_admin.deleted:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': 'admin account has been deleted, contact super admin'
                }), 403

            if not check_admin.check_password(password):
                return jsonify({
                    'code': 401,
                    'code_message': 'unauthorized',
                    'message': 'invalid password'
                }), 401

            extra_payload = {
                'sub': str(check_admin.id),
                'given_name': check_admin.first_name,
                'family_name': check_admin.last_name,
            }

            jti = secrets.token_urlsafe(16)

            access_token = encode_token(extra_payload, jti, config.access_token_time, config.access_secret_key)
            refresh_token = encode_token(extra_payload, jti, config.refresh_token_time, config.refresh_secret_key)

            check_admin.jti = Cryptographer.encrypt(jti)
            check_admin.save()

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'message': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires': (datetime.now() + timedelta(seconds=config.access_token_time)).strftime('%I:%M %p'),
                    'refresh_token_expires': (
                            datetime.now() + timedelta(seconds=config.refresh_token_time)).strftime(
                        '%B %d, %Y at %I:%M %p'),
                    'id': str(check_admin.id),
                    'message': f'{check_admin.first_name} logged in successfully',
                    'email_verified': check_admin.email_verified,
                    'account_active': check_admin.account_active,
                    'account_deleted': check_admin.deleted
                }
            })

        except DataError:
            return jsonify({
                "code": 400,
                'code_message': 'bad request',
                "message": "this error is a datatype error",
            }), 400

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "message": "this error is a database error",
            }), 500

    @staticmethod
    def refresh_token():
        """
        Generate a new access token using a valid refresh token from cookies

        Returns:
            Flask response with new access token or error message
        """
        try:
            # Get refresh token from cookie

            refresh_token = request.cookies.get('refresh_token')

            if request.is_json and request.content_length and request.content_length > 0:
                refresh_token = request.get_json().get('refresh_token')

            if not refresh_token:
                return jsonify({
                    "code": 401,
                    "code_message": "unauthorized",
                    "message": "Refresh token is missing"
                }), 401

            # Decode and verify the refresh token
            decoded_token = decode_token(refresh_token, config.refresh_secret_key)

            if "status" in decoded_token and decoded_token["status"] in ["invalid"]:
                return jsonify({
                    "code": 401,
                    "code_message": "unauthorized",
                    "message": "Invalid refresh token"
                }), 401

            if "status" in decoded_token and decoded_token["status"] in ["expired"]:
                return jsonify({
                    "code": 401,
                    "code_message": "unauthorized",
                    "message": "Expired refresh token"
                }), 401

            # Get user ID from the decoded refresh token
            user_id = decoded_token['sub']

            # Fetch the user to get their current role and status
            user = UserModel.query.filter_by(id=user_id).first()

            if not user:
                return jsonify({
                    "code": 404,
                    'code_message': 'not found',
                    "message": "The requested customer was not found",
                }), 404

            if not user.email_verified:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': 'email not verified'
                }), 403

            if not user.account_active:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'message': 'User account is not active'
                }), 400

            if user.deleted:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': 'user account has been deleted, contact admin'
                }), 403

            # Create payload for the new access token
            extra_payload = {
                'sub': str(user.id),
                'given_name': user.first_name,
                'family_name': user.last_name,
            }

            jti = secrets.token_urlsafe(16)

            # Generate new access token
            access_token = encode_token(extra_payload, jti, config.access_token_time, config.access_secret_key)
            refresh_token = encode_token(extra_payload, jti, config.refresh_token_time, config.refresh_secret_key)

            # Build response body
            response_body = {
                'code': 200,
                'code_message': 'successful',
                'message': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires': (datetime.now() + timedelta(seconds=config.access_token_time)).strftime('%I:%M %p'),
                    'refresh_token_expires': (
                            datetime.now() + timedelta(seconds=config.refresh_token_time)).strftime(
                        '%B %d, %Y at %I:%M %p'),
                    'email_verified': user.email_verified,
                    'account_active': user.account_active,
                    'account_deleted': user.deleted
                }
            }

            # Create a response object
            response = make_response(jsonify(response_body))

            # Set secure HTTP-only cookie for access token
            response.set_cookie(
                'access_token', access_token,
                httponly=False if config.debug is True else True,
                secure=False if config.debug is True else True,  # Only over HTTPS
                samesite='None',  # Prevent CSRF
                max_age=config.access_token_time
            )

            # Set secure HTTP-only cookie for refresh token
            response.set_cookie(
                'refresh_token', refresh_token,
                httponly=False if config.debug is True else True,
                secure=False if config.debug is True else True,
                samesite='None',
                max_age=config.refresh_token_time
            )

            user.jti = Cryptographer.encrypt(jti)
            user.save()

            return response


        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "message": "this error is a database error",
            }), 500
