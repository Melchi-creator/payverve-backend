"""
app/utilities/authorisation.py
the authorisation module is used to check if the user is authenticated
"""

from functools import wraps

import jwt
from flask import jsonify, request

from config import access_secret_key
from src.models import AdminModel, UserModel
from src.utilities import decode_token


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Extract token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                try:
                    token = auth_header.split(' ')[1].encode('utf-8')

                except IndexError:
                    return jsonify({
                        "code": 401,
                        "code_message": "Authentication token is missing",
                        "message": "Token not found in Authorization header"
                    }), 401

        if not token:
            return jsonify({
                "code": 401,
                "code_message": "Authentication token is missing",
                "message": "Token not found in Authorization header"
            }), 401

        try:

            current_user = decode_token(token, access_secret_key)

            if "status" in current_user and current_user["status"] in ["expired"]:  # noqa
                return jsonify({
                    'code': 401,
                    "code_message": "Verification failed. Expired Token",
                    "message": "Expired Token"
                }), 401

            if "status" in current_user and current_user["status"] in ["invalid"]:  # noqa
                return jsonify({
                    'code': 401,
                    "code_message": "Verification failed. Expired Token",
                    "message": "Invalid token"
                }), 401

            # Check if the token has a valid user ID

            if 'sub' not in current_user:
                return jsonify({
                    "code": 401,
                    "code_message": "Authentication token is invalid",
                    "message": "Token does not contain user ID"
                }), 401

            user_id = current_user['sub']

            checked_user = None

            checked_customer = UserModel.query.filter_by(id=user_id).first()

            if checked_customer:
                checked_user = checked_customer

            checked_admin = AdminModel.query.filter_by(id=user_id).first()

            if checked_admin:
                checked_user = checked_admin

            if not checked_user:
                return jsonify({
                    "code": 404,
                    "code_message": "not found",
                    "message": "The requested user was not found"
                }), 404

            if not checked_user.email_verified:
                return jsonify({
                    "code": 403,
                    "code_message": "forbidden",
                    "message": "User is not verified"
                }), 403

            if not checked_user.account_active:
                return jsonify({
                    "code": 403,
                    "code_message": "forbidden",
                    "message": "Your account is not active"
                }), 403

            if checked_user.deleted:
                return jsonify({
                    "code": 403,
                    "code_message": "forbidden",
                    "message": "Your account has been deleted"
                }), 403

            # Add the current user to the request context
            request.current_user = current_user


        except jwt.ExpiredSignatureError:
            return jsonify({
                'code': 401,
                "code_message": "Verification failed. Expired Token",
                "message": "Expired Token"
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                'code': 401,
                "code_message": "Verification failed. Expired Token",
                "message": "Invalid token"
            }), 401

        return f(*args, **kwargs)

    return decorated
