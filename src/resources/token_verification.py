"""
src/resources/token_verification.py
This module contains the TokenVerificationRepository class, which is used to interact with the TokenVerificationModel
"""
import secrets
from datetime import datetime, timedelta
from hmac import compare_digest

from flask import jsonify, render_template
from flask_restful import Resource
from flask_restful.reqparse import Argument
from psycopg2 import InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DBAPIError, DisconnectionError

import config
from ..middlewares import MailtrapHelper
from ..models import AdminModel, UserModel
from ..models.token_verification import TokenVerificationModel
from ..utilities import Cryptographer, parse_params
from ..value_object import EmailCheck, PasswordValidation


class TokenVerification(Resource):
    """ this class is used to interact with the TokenVerificationModel """

    @staticmethod
    def read():
        """ this method is used to get all the token verifications """

        try:

            token_verifications = TokenVerificationModel.query.order_by(
                TokenVerificationModel.created_at.desc()).all()

            if not token_verifications:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no token found'
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
                    'created_at': token_verification.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': token_verification.updated_at.strftime("%d %b %Y, %I:%M %p") if token_verification.updated_at else None,
                }
                for token_verification in token_verifications
            ]

            return jsonify({
                'code': 200,
                'status_message': 'successful',
                'data': data
            }), 200

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'status_message': 'database error',
                'message': "this error is a database error",
            }), 500

    @staticmethod
    @parse_params(
        Argument("email_address", location="json", required=True),
    )
    def request_password_reset(email_address):
        """ """

        try:

            EmailCheck(email_address)

            checked_user = None

            checked_customer = UserModel.query.filter_by(
                email_address=email_address).first()

            if checked_customer:
                checked_user = checked_customer

            checked_admin = AdminModel.query.filter_by(
                email_address=email_address).first()

            if checked_admin:
                checked_user = checked_admin

            if not checked_user:
                return jsonify({
                    'code': 404,
                    'status_message': 'not_found',
                    'message': f'{email_address} email address does not have an account'
                }), 404

            if not checked_user.email_verified:
                return jsonify({
                    "code": 403,
                    'status_message': "forbidden",
                    'message': "User is not verified"
                }), 403

            if not checked_user.account_active:
                return jsonify({
                    "code": 403,
                    'status_message': "forbidden",
                    'message': "Your account is not active"
                }), 403

            if checked_user.deleted:
                return jsonify({
                    "code": 403,
                    'status_message': "forbidden",
                    'message': "Your account has been deleted"
                }), 403

            verification_code = str(secrets.randbelow(1000000)).zfill(6)

            print("=" * 60)
            print(f"EMAIL VERIFICATION CODE: {verification_code}")
            print("=" * 60)

            # noinspection PyArgumentList
            new_verification_code = TokenVerificationModel(
                channel='email',
                channel_contact=email_address,
                code_sent=Cryptographer.encrypt(verification_code),
                expiration_time=900,
                timestamp=datetime.now(),
                status='pending'
            )

            print("=" * 60)
            print(f"EMAIL VERIFICATION CODE: {new_verification_code}")
            print("=" * 60)

            new_verification_code.save()

            checked_user.password_reset_code = verification_code
            checked_user.save()

            expiry_time = new_verification_code.timestamp + \
                timedelta(seconds=new_verification_code.expiration_time)
            current_year = datetime.now().year

            endpoint = '/send'
            receipient = [
                {"email": checked_user.email_address,
                 "name": f"{checked_user.first_name} {checked_user.last_name}"},
            ]
            subject = "Password Reset Notification"
            mail_status_message = render_template(
                'customer/password_reset.html',
                first_name=checked_user.first_name,
                last_name=checked_user.last_name,
                user_email_address=checked_user.email_address,
                current_year=current_year,
                expiry_time=expiry_time.strftime("%I:%M %p"),
                verification_code=verification_code
            )

            MailtrapHelper.mailtrap_email_sender(config.mailtrap_payverve_security_name,
                                                 config.mailtrap_payverve_security_email,
                                                 endpoint,
                                                 receipient,
                                                 subject,
                                                 mail_status_message)

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': f'password reset code has been sent to {checked_user.email_address}'
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

        except ValueError as e:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - type error',
                'message': str(e)
            }), 400

    @staticmethod
    @parse_params(
        Argument("password", location="json", required=True),
        Argument("verification_code", location="json", required=True),
    )
    def verify_password_reset(password, verification_code):
        """ """

        try:

            if not verification_code:
                return jsonify({
                    "code": 401,
                    'status_message': "Verification code is missing",
                    'message': "Verification code not found in request"
                }), 401

            if len(verification_code) != 6:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'verification code must be 6 digits'
                }), 400

            if not password:
                return jsonify({
                    "code": 400,
                    'status_message': "Bad request",
                    'message': "New password is required"
                }), 400

            PasswordValidation(password)

            checked_user = None
            checked_customer = UserModel.query.filter_by(
                password_reset_code=verification_code).first()

            if checked_customer:
                checked_user = checked_customer

            checked_admin = AdminModel.query.filter_by(
                password_reset_code=verification_code).first()

            if checked_admin:
                checked_user = checked_admin

            if not checked_user:
                return jsonify({
                    "code": 404,
                    'status_message': "not found",
                    'message': "no current request for a password reset or inccorrect verification code"
                }), 404

            if not checked_user.email_verified:
                return jsonify({
                    "code": 403,
                    'status_message': "forbidden",
                    'message': "User is not verified"
                }), 403

            if not checked_user.account_active:
                return jsonify({
                    "code": 403,
                    'status_message': "forbidden",
                    'message': "Your account is not active"
                }), 403

            if checked_user.deleted:
                return jsonify({
                    "code": 403,
                    'status_message': "forbidden",
                    'message': "Your account has been deleted"
                }), 403

            confirmation = TokenVerificationModel.query.filter_by(
                channel="email",
                channel_contact=checked_user.email_address,
            ).order_by(TokenVerificationModel.created_at.desc()).first()

            if not confirmation:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'verification code not found'
                }), 400

            confirmation_code = confirmation.code_sent
            decrypt_confirmation_code = Cryptographer.decrypt(
                confirmation_code)

            if not compare_digest(decrypt_confirmation_code, verification_code):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'verification code does not match, try again'
                }), 400

            expected_expiry = confirmation.timestamp + \
                timedelta(seconds=confirmation.expiration_time)

            if expected_expiry < datetime.now():
                confirmation.status = 'expired'
                confirmation.save()

                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'this code has expired'
                }), 403

            if confirmation.status == "verified":
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'this code has been verified'
                }), 400

            confirmation.status = 'verified'
            confirmation.save()

            checked_user.set_password(password)
            checked_user.password_reset_code = None
            checked_user.save()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'password reset successful'
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

        except ValueError as e:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - type error',
                'message': str(e)
            }), 400
