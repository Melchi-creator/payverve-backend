"""
src/resources/user.py
This module defines the UserResource class, which provides CRUD operations for user accounts.
It includes methods for creating, reading, updating, and deleting user accounts,
as well as handling errors related to database operations.
"""
import secrets
from datetime import datetime, timedelta

import requests
from flask import jsonify, render_template
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DBAPIError, DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, SQLAlchemyError

import config
from ..models import CurrencyModel, UserModel
from ..models.token_verification import TokenVerificationModel
from ..utilities import Cryptographer, MailtrapHelper, parse_params
from ..value_object import EmailCheck, PasswordValidation


class UserResource(Resource):
    """ This class is concerned with User Resources """

    @staticmethod
    @parse_params(
        Argument("first_name", location="json", required=True),
        Argument("last_name", location="json", required=True),
        Argument("email_address", location="json", required=True),
        Argument("mobile_number", location="json", required=True),
        Argument("password", location="json", required=True),
        Argument("gender", location="json", required=True),
        Argument("date_of_birth", location="json", required=True),
    )
    def create(first_name, last_name, email_address, mobile_number, password, gender, date_of_birth):
        """ Creates users account """

        try:

            EmailCheck(email_address)
            PasswordValidation(password)

            gender_check = ["male", "female"]

            if gender.lower() not in gender_check:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'data': "gender must be either 'male' or 'female'"
                }), 400

            user_model = UserModel.query
            user_email = user_model.filter_by(email_address=email_address).first()
            user_number = user_model.filter_by(mobile_number=mobile_number).first()

            if user_email:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'data': 'email address already has an account'
                }), 409

            if user_number:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'data': 'mobile number already has an account'
                }), 409

            parsed_date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').year
            age = int(datetime.now().year) - int(parsed_date_of_birth)

            if age < 17:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'data': 'you must be 17 years and above'
                }), 400

            # noinspection PyArgumentList
            new_user = UserModel(
                first_name=first_name,
                last_name=last_name,
                email_address=email_address,
                mobile_number=mobile_number,
                gender=gender,
                date_of_birth=date_of_birth
            )
            new_user.set_password(password)
            new_user.save()

            payload = {
                'user_id': str(new_user.id),
                'currency_id': str(CurrencyModel.query.filter_by(short_code='ngn').first().id)
            }

            response = requests.request("POST", f'{config.app_path}/wallets', json=payload)

            if response.status_code != 201:
                user_to_delete = UserModel.query.filter_by(id=new_user.id).first()
                user_to_delete.delete()

                return jsonify({
                    'code': response.status_code,
                    'code_status': response.json().get('code_status', 'error'),
                    'data': response.json().get('data', 'an error occurred while creating wallet')
                }), response.status_code

            # send verification and welcome email

            # verification email

            verification_code = str(secrets.randbelow(1000000)).zfill(6)

            # noinspection PyArgumentList
            new_verification_code = TokenVerificationModel(
                channel='email',
                channel_contact=new_user.email_address,
                code_sent=Cryptographer.encrypt(verification_code),
                expiration_time=300,
                timestamp=datetime.now(),
                status='pending'
            )

            new_verification_code.save()

            expiry_time = new_verification_code.timestamp + timedelta(seconds=new_verification_code.expiration_time)

            current_year = datetime.now().year

            endpoint = '/send'
            receipient = [
                {"email": new_user.email_address,
                 "name": f"{new_user.first_name} {new_user.last_name}"},
            ]
            subject = f"{new_user.first_name} Confirm your Account"
            mail_message = render_template(
                'customer/email_verification.html',
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                verification_code=verification_code,
                user_email_address=new_user.email_address,
                current_year=current_year,
                expiry_time=expiry_time.strftime("%I:%M %p"),
            )

            MailtrapHelper.mailtrap_email_sender(endpoint,
                                                 receipient,
                                                 subject,
                                                 mail_message)

            # welcome email

            current_year = datetime.now().year

            endpoint = '/send'
            receipient = [
                {"email": new_user.email_address,
                 "name": f"{new_user.first_name} {new_user.last_name}"},
            ]
            subject = f"Welcome to Payverve, {new_user.first_name} – Your Boardless Journey Starts Here 🌱"
            mail_message = render_template(
                'customer/email_welcome.html',
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                user_email_address=new_user.email_address,
                current_year=current_year,
            )

            MailtrapHelper.mailtrap_email_sender(endpoint,
                                                 receipient,
                                                 subject,
                                                 mail_message)

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'account was successfully created'
            }), 201

        except ValueError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'data': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'data': str(e)
            }), 400

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'data': 'account already has an account'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - data error',
                'data': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'data': 'could not fetch table'
            }),

    @staticmethod
    @parse_params(
        Argument("email_address", location="json", required=True),
        Argument("verification_code", location="json", required=True),
    )
    def email_otp_base_verification(verification_code: str, email_address: str):
        """ this method is used to verify the email address of a user """

        try:

            EmailCheck(email_address)

            if len(verification_code) != 6:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'verification code must be 6 digits'
                }), 400

            customer = UserModel.query.filter_by(email_address=email_address).first()

            if not customer:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': f'no account with {email_address} was found'
                }), 404

            if customer.email_verified:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'this user is already verified'
                }), 400

            confirmation = TokenVerificationModel.query.filter_by(
                channel="email",
                channel_contact=email_address,
            ).order_by(TokenVerificationModel.created_at.desc()).first()

            if not confirmation:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'verification code not found'
                }), 400

            confirmation_code = confirmation.code_sent
            decrypt_confirmation_code = Cryptographer.decrypt(confirmation_code)

            if decrypt_confirmation_code != verification_code:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'verification code does not match, try again'
                }), 400

            expected_expiry = confirmation.timestamp + timedelta(seconds=confirmation.expiration_time)

            if expected_expiry < datetime.now():
                confirmation.status = 'expired'
                confirmation.save()

                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'data': 'this code has expired'
                }), 403

            if confirmation.status == "verified":
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'this code has been verified'
                }), 400

            confirmation.status = 'verified'
            confirmation.save()

            customer.email_verified = True
            customer.save()

            return jsonify({
                'code': 200,
                'code_status': 'successful',
                'data': 'verification was successful'
            }), 200

        except ValueError as e:
            return jsonify({
                'code': 500,
                'code_message': 'value error',
                'data': f'an incorrect value was inputted: {str(e)}',
            }), 500

        except DataError:
            return jsonify({
                'code': 400,
                'code_message': 'bad request',
                'data': 'this error is a datatype error',
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
    )
    def resend_email_otp_base_verification(email_address: str):
        """ this method is used to resend the email verification token """

        try:

            EmailCheck(email_address)

            customer = UserModel.query.filter_by(email_address=email_address).first()

            if not customer:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': f'no account with {email_address} was found'
                }), 404

            if customer.email_verified:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'this user is already verified'
                }), 400

            confirmation = TokenVerificationModel.query.filter_by(
                channel="email",
                channel_contact=email_address,
                status='pending',
            ).order_by(TokenVerificationModel.created_at.desc()).first()

            if confirmation:
                expected_expiry = confirmation.timestamp + timedelta(seconds=confirmation.expiration_time)

                if expected_expiry > datetime.now():
                    return jsonify({
                        'code': 400,
                        'code_message': 'bad request',
                        'data': 'the previous code has not expire yet'
                    }), 400

            confirmation.status = 'expired'
            confirmation.save()

            # resend verification email

            verification_code = str(secrets.randbelow(1000000)).zfill(6)

            # noinspection PyArgumentList
            new_verification_code = TokenVerificationModel(
                channel='email',
                channel_contact=email_address,
                code_sent=Cryptographer.encrypt(verification_code),
                expiration_time=300,
                timestamp=datetime.now(),
                status='pending'
            )

            new_verification_code.save()

            expiry_time = new_verification_code.timestamp + timedelta(seconds=new_verification_code.expiration_time)

            current_year = datetime.now().year

            endpoint = '/send'
            receipient = [
                {"email": email_address, "name": f"{customer.first_name} {customer.last_name}"},
            ]
            subject = f"{customer.first_name} Verify your Account"
            mail_message = render_template(
                'customer/email_verification.html',
                first_name=customer.first_name,
                last_name=customer.last_name,
                verification_code=verification_code,
                user_email_address=email_address,
                current_year=current_year,
                expiry_time=expiry_time.strftime("%I:%M %p"),
            )

            MailtrapHelper.mailtrap_email_sender(endpoint,
                                                 receipient,
                                                 subject,
                                                 mail_message)

            return jsonify({
                'code': 200,
                'code_status': 'successful',
                'data': 'verification code sent successfully'
            }), 200

        except ValueError as e:
            return jsonify({
                'code': 500,
                'code_message': 'value error',
                'data': f'an incorrect value was inputted: {str(e)}',
            }), 500

        except DataError:
            return jsonify({
                'code': 400,
                'code_message': 'bad request',
                'data': 'this error is a datatype error',
            }), 400

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "data": "this error is a database error",
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all users account """

        users = UserModel.query.all()

        try:
            if not users:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
                }), 404

            data = []

            for user in users:
                data.append({
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'middle_name': user.middle_name,
                    'username': user.username,
                    'email_address': user.email_address,
                    'mobile_number': user.mobile_number,
                    'password': user.password,
                    'auth_pin': user.auth_pin,
                    'transaction_pin': user.transaction_pin,
                    'gender': user.gender,
                    'date_of_birth': user.date_of_birth,
                    'house_number': user.house_number,
                    'street_name': user.street_name,
                    'city': user.city,
                    'state': user.state,
                    'zipcode': user.zipcode,
                    'country': user.country,
                    'photo': user.photo,
                    'deleted': user.deleted,
                })

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': data
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

    @staticmethod
    def read_one(id=None):
        """ Retrieve a user account by id """

        user = UserModel.query.filter_by(id=id).first()

        try:
            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
                }), 404

            data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'middle_name': user.middle_name,
                'username': user.username,
                'email_address': user.email_address,
                'mobile_number': user.mobile_number,
                'password': user.password,
                'auth_pin': user.auth_pin,
                'transaction_pin': user.transaction_pin,
                'gender': user.gender,
                'date_of_birth': user.date_of_birth,
                'house_number': user.house_number,
                'street_name': user.street_name,
                'city': user.city,
                'state': user.state,
                'zipcode': user.zipcode,
                'country': user.country,
                'photo': user.photo,
                'deleted': user.deleted,
            }

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': data
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

    @staticmethod
    @parse_params(
        Argument("first_name", location="json"),
        Argument("last_name", location="json"),
        Argument("middle_name", location="json"),
        Argument("username", location="json"),
        Argument("email_address", location="json"),
        Argument("mobile_number", location="json"),
        Argument("password", location="json"),
        Argument("auth_pin", location="json"),
        Argument("transaction_pin", location="json"),
        Argument("gender", location="json"),
        Argument("date_of_birth", location="json"),
        Argument("house_number", location="json"),
        Argument("street_name", location="json"),
        Argument("city", location="json"),
        Argument("state", location="json"),
        Argument("zipcode", location="json"),
        Argument("country", location="json"),
        Argument("photo", location="json"),
        Argument("deleted", location="json", type='bool'),
    )
    def update(id=None, **fields):
        """ Updates a user account by id """

        user = UserModel.query.filter_by(id=id).first()

        try:
            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
                }), 404

            if 'first_name' in fields and fields['first_name'] is not None:
                user.first_name = fields['first_name']

            if 'last_name' in fields and fields['last_name'] is not None:
                user.last_name = fields['last_name']

            if 'middle_name' in fields and fields['middle_name'] is not None:
                user.middle_name = fields['middle_name']

            if 'username' in fields and fields['username'] is not None:
                user.username = fields['username']

            if 'email_address' in fields and fields['email_address'] is not None:
                user.email_address = fields['email_address']

            if 'mobile_number' in fields and fields['mobile_number'] is not None:
                user.mobile_number = fields['mobile_number']

            if 'password' in fields and fields['password'] is not None:
                user.set_password(fields['password'])

            if 'auth_pin' in fields and fields['auth_pin'] is not None:
                user.set_auth_pin(fields['auth_pin'])

            if 'transaction_pin' in fields and fields['transaction_pin'] is not None:
                user.set_transaction_pin(fields['transaction_pin'])

            if 'gender' in fields and fields['gender'] is not None:
                user.gender = fields['gender']

            if 'date_of_birth' in fields and fields['date_of_birth'] is not None:
                user.date_of_birth = fields['date_of_birth']

            if 'house_number' in fields and fields['house_number'] is not None:
                user.house_number = fields['house_number']

            if 'street_name' in fields and fields['street_name'] is not None:
                user.street_name = fields['street_name']

            if 'city' in fields and fields['city'] is not None:
                user.city = fields['city']

            if 'state' in fields and fields['state'] is not None:
                user.state = fields['state']

            if 'zipcode' in fields and fields['zipcode'] is not None:
                user.zipcode = fields['zipcode']

            if 'country' in fields and fields['country'] is not None:
                user.country = fields['country']

            if 'photo' in fields and fields['photo'] is not None:
                user.photo = fields['photo']

            if 'deleted' in fields and fields['deleted'] is not None:
                user.deleted = fields['deleted']

            user.save()

            data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'middle_name': user.middle_name,
                'username': user.username,
                'email_address': user.email_address,
                'mobile_number': user.mobile_number,
                'password': user.password,
                'auth_pin': user.auth_pin,
                'transaction_pin': user.transaction_pin,
                'gender': user.gender,
                'date_of_birth': user.date_of_birth,
                'house_number': user.house_number,
                'street_name': user.street_name,
                'city': user.city,
                'state': user.state,
                'zipcode': user.zipcode,
                'country': user.country,
                'photo': user.photo,
                'deleted': user.deleted,
            }

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': data
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

    @staticmethod
    def delete(id=None):
        """ Retrieve and delete a user account by id """

        user = UserModel.query.filter_by(id=id).first()

        try:
            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
                }), 404

            if user.deleted:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'data': 'account is already staged for deleting'
                }), 400

            # user.deleted = True
            # user.deleted_date = datetime.now()
            # user.save()

            user.delete()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'account has been staged for deleting'
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

# """
# user.py
#
# Defines all functions for users especially CRUD
# """
# from flask import jsonify
# from flask_restful import Resource
# from flask_restful.reqparse import Argument
# from sqlalchemy.exc import DataError, \
#     DisconnectionError, \
#     IntegrityError, \
#     InternalError, \
#     OperationalError, \
#     ProgrammingError, SQLAlchemyError
#
# # from ..middlewares.auth import auth
# from ..models import CurrencyModel, UserModel, WalletModel
# # from ..utilities import RandomGenerator, emailHandler, parse_params, validation
# from ..utilities import RandomGenerator, parse_params
#
#
# class UserResource(Resource):
#     """ This class is concern with User Resources """
#
#     @staticmethod
#     @parse_params(
#         Argument("first_name", location="json", required=True),
#         Argument("last_name", location="json", required=True),
#         Argument("email_address", location="json", required=True),
#         Argument("mobile_number", location="json", required=True),
#         Argument("password", location="json", required=True),
#         Argument("gender", location="json", required=True),
#         Argument("date_of_birth", location="json", required=True),
#     )
#     def create(first_name, last_name, email_address, mobile_number, password, gender, date_of_birth):
#         """ Creates users account """
#
#         user_model = UserModel.query
#         user_email = user_model.filter_by(email_address=email_address).first()
#         user_number = user_model.filter_by(mobile_number=mobile_number).first()
#
#         if user_email:
#             return jsonify({
#                 'code': 409,
#                 'code_status': 'conflict',
#                 'data': 'email address already has an account'
#             }), 409
#
#         if user_number:
#             return jsonify({
#                 'code': 409,
#                 'code_status': 'conflict',
#                 'data': 'mobile number already has an account'
#             }), 409
#
#         # age = datetime.now() - date_of_birth
#         #
#         # if age < 17:
#         #     return jsonify({
#         #         'code': 400,
#         #         'code_status': 'bad request',
#         #         'data': 'you must be 17 years and above'
#         #     }), 400
#
#         # noinspection PyArgumentList
#         new_user = UserModel(
#             first_name=first_name,
#             last_name=last_name,
#             email_address=email_address,
#             mobile_number=mobile_number,
#             gender=gender,
#             date_of_birth=date_of_birth
#         )
#         new_user.set_password(password)
#         new_user.save()
#
#         naira_currency = CurrencyModel.query.filter_by(short_code='ngn').first()
#
#         # noinspection PyArgumentList
#         new_wallet = WalletModel(
#             fund=0,
#             account_number=RandomGenerator.wallet_account_number(),
#             user=new_user.id,
#             currency=naira_currency.id
#         )
#         new_wallet.save()
#
#         # # function to generate account validation token
#         # token = validation.generate_token(new_user.get_id())
#         # verification_url = config.base_url + url_for('user.verify_email', token=token)
#         # verification_template = render_template('welcome.html', first_name=new_user.first_name, token=verification_url)
#         # verification_data = {
#         #     'recipient':new_user.email_address,
#         #     'subject': 'Welcome to PayVerve',
#         #     'template': verification_template
#         # }
#         #
#         # context = {
#         #     'wallet_id':new_wallet.account_number,
#         #     'username': new_user.first_name,
#         #     'wallet_created_at': new_wallet.created_at.strftime('%a %d %b %Y, %I:%M%p'),
#         #     'currency': naira_currency.name
#         # }
#         # account_template = render_template('wallet.html', **context)
#         # data = {
#         #     'recipient':new_user.email_address,
#         #     'subject': 'New Wallet Created',
#         #     'template': account_template
#         # }
#
#         # print("context >>> ", context)
#
#         # Mail sending should be handled as background task
#         # TODO: Integrete with Celery/Redis for task scheduling
#         # emailHandler.sendMail(**verification_data)
#         # emailHandler.sendMail(**data)
#
#         return jsonify({
#             'code': 201,
#             'code_status': 'created',
#             'data': 'account was successfully created',
#             # 'token':token
#         }), 201
#
#     # @staticmethod
#     # @parse_params(
#     #     Argument("email_address", location="json", required=True),
#     #     Argument("password", location="json", required=True),
#     # )
#     # def login(email_address, password):
#     #     """ Retrieve a user account by id """
#     #
#     #     user = UserModel.query.filter_by(email_address=email_address).first()
#     #
#     #     if not user:
#     #         return jsonify({
#     #             'code': 404,
#     #             'code_status': 'data not found',
#     #             'data': 'no account was found'
#     #         }), 404
#     #
#     #     if user and user.check_password(password=password):
#     #         return auth.login(user=user)
#     #
#     #     return jsonify({
#     #         'code': 401,
#     #         'code_status': 'Invalid credentials',
#     #     }), 401
#     #
#     # @staticmethod
#     # @auth.login_required
#     # def logout(**kwargs):
#     #     """ Logs out the user account"""
#     #     return auth.logout()
#     #
#     # @staticmethod
#     # def verify_email(token=None):
#     #     user_id = validation.verify_token(token)
#     #     user = UserModel.query.filter_by(id=user_id).first()
#     #     if user:
#     #         user.email_verified = True
#     #         user.save()
#     #         return jsonify({
#     #             "code": 200,
#     #             "status": "Account verified"
#     #         }), 200
#     #
#     #     return ({
#     #         "code": 400,
#     #         "status": "Invalid Token!"
#     #     }), 400
#     #
#     # @staticmethod
#     # @parse_params(
#     #     Argument("email_address", location="json", required=True),
#     # )
#     # def request_password_reset(email_address):
#     #     user = UserModel.query.filter_by(email_address=email_address).first()
#     #
#     #     if not user:
#     #         return jsonify({
#     #             'code': 404,
#     #             'code_status': 'data not found',
#     #             'data': 'no account with that email'
#     #         }), 404
#     #
#     #     token = validation.generate_token(user.get_id(), context='reset-password')
#     #     # request url should be deeplink to app
#     #     reset_url = config.mobile_app_path + url_for('user.verify_reset_token', token=token)
#     #     date_time = datetime.now().strftime('%a %d %b %Y, %I:%M%p')
#     #     date, time = date_time.split(', ')
#     #
#     #     context = {
#     #         'first_name': user.first_name,
#     #         'reset_link': reset_url,
#     #         'date': date,
#     #         'time': time
#     #     }
#     #     print(context)
#     #
#     #     reset_template = render_template('resetpassword.html', **context)
#     #     reset_data = {
#     #         'recipient': user.email_address,
#     #         'subject': 'Account Login',
#     #         'template': reset_template
#     #     }
#     #
#     #     # Mail sending should be handled as background task
#     #     # TODO: Integrete with Celery/Redis for task scheduling
#     #     emailHandler.sendMail(**reset_data)
#     #
#     #     return jsonify({
#     #         'code': 200,
#     #         'code_status': 'email sent',
#     #         'data': 'reset link sent to registered email',
#     #         'url': reset_url
#     #     }), 200
#     #
#     # @staticmethod
#     # def verify_reset_token():
#     #     token = request.args.get('token')
#     #     user_id = validation.verify_token(token=token, context='reset-password')
#     #     user = UserModel.query.filter_by(id=user_id).first()
#     #
#     #     if not user:
#     #         return jsonify({
#     #             'code': 401,
#     #             'data': "Token is invalid or expired!"
#     #         }), 401
#     #
#     #     return jsonify({
#     #         'code': 202,
#     #         'data': 'Token is valid',
#     #     }), 202
#     #
#     # @staticmethod
#     # @parse_params(
#     #     Argument("new_password", location="json", required=True),
#     #     Argument("token", location="json", required=True),
#     # )
#     # def reset_password(new_password=None, token=None):
#     #     token = token if request.method == 'POST' else request.args.get('token')
#     #     user_id = validation.verify_token(token=token, context='reset-password')
#     #     user = UserModel.query.filter_by(id=user_id).first()
#     #
#     #     if not user:
#     #         return jsonify({
#     #             'code': 401,
#     #             'data': "Token is invalid or expired!"
#     #         }), 401
#     #
#     #     user.set_password(password=new_password)
#     #     user.save()
#     #
#     #     return jsonify({
#     #         'code': 200,
#     #         'data': 'password reset successful',
#     #     }), 200
