"""
src/resources/user.py
This module defines the UserResource class, which provides CRUD operations for user accounts.
It includes methods for creating, reading, updating, and deleting user accounts,
as well as handling errors related to database operations.
"""
import secrets
import string
from datetime import datetime, timedelta
from secrets import compare_digest

import requests
from flask import jsonify, render_template
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DBAPIError, DataError, \
    DisconnectionError, \
    IntegrityError, InternalError, \
    OperationalError, \
    ProgrammingError, SQLAlchemyError

import config
from ..middlewares import MailtrapHelper
from ..models import CurrencyModel, UserModel, WalletModel
from ..models.token_verification import TokenVerificationModel
from ..utilities import Cryptographer, parse_params
from ..value_object import EmailCheck, MinimumBalance, PasswordValidation


class UserResource(Resource):
    """ This class is concerned with User Resources """

    @staticmethod
    @parse_params(
        Argument("first_name", location="json", required=True),
        Argument("last_name", location="json", required=True),
        Argument("username", location="json", required=True),
        Argument("email_address", location="json", required=True),
        Argument("mobile_number", location="json", required=True),
        Argument("password", location="json", required=True),
        Argument("referral_code", location="json"),
    )
    def create(first_name, last_name, email_address, mobile_number, password, username, referral_code):
        """ Creates users account """

        try:

            EmailCheck(email_address)
            PasswordValidation(password)

            user_model = UserModel.query
            user_email = user_model.filter_by(email_address=email_address).first()

            if user_email:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'message': 'email address already has an account'
                }), 409

            user_mobile_number = user_model.filter_by(mobile_number=mobile_number).first()

            if user_mobile_number:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'message': 'mobile number already has an account'
                }), 409

            username_check = user_model.filter_by(username=username.lower()).first()

            if username_check:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'message': 'username already exist'
                }), 409

            alphabet = string.ascii_letters + string.digits
            user_code = ''.join(secrets.choice(alphabet) for _ in range(11))

            # noinspection PyArgumentList
            new_user = UserModel(
                first_name=first_name,
                last_name=last_name,
                email_address=email_address,
                username=username.lower(),
                mobile_number=mobile_number,
                user_code=user_code
            )
            new_user.set_password(password)
            new_user.save()

            payload = {
                'user_id': str(new_user.id),
                'currency_id': str(CurrencyModel.query.filter_by(short_code='ngn').first().id),
                'created_by_payverve': True,
                'email_address': new_user.email_address,
            }

            response = requests.request("POST", f'{config.app_path}/inapp-wallets', json=payload)

            if response.status_code != 201:
                user_to_delete = UserModel.query.filter_by(id=new_user.id).first()
                user_to_delete.delete()

                return jsonify({
                    'code': response.status_code,
                    'code_status': response.json().get('code_status', 'error'),
                    'message': response.json().get('data', 'an error occurred while creating wallet')
                }), response.status_code

            referral_confirmation_id = None

            if referral_code:
                referral_confirmation = UserModel.query.filter_by(user_code=referral_code).first()
                referral_confirmation_id = referral_confirmation.id

                if not referral_confirmation:
                    return jsonify({
                        'code': 404,
                        'code_status': 'not found',
                        'message': 'there is no user with that referral code'
                    }), 404

                payload = {
                    'referral_id': str(referral_confirmation.id),
                    'referral_code': referral_confirmation.user_code,
                    'referred_id': str(new_user.id),
                    'referred_code': new_user.user_code,
                    'created_by_payverve': True,
                    'email_address': new_user.email_address,
                }

                referral_response = requests.request("POST", f'{config.app_path}/referrals', json=payload)

                if referral_response.status_code != 201:
                    ngn_wallet = CurrencyModel.query.filter_by(short_code='ngn').first().id
                    referral_wallet = WalletModel.query.filter_by(user_id=referral_confirmation.id,
                                                                  currency_id=ngn_wallet).first()

                    decrypted_referral_fund = Cryptographer.decrypt(referral_wallet.fund)
                    current_decrypted_referral_fund = float(decrypted_referral_fund)

                    MinimumBalance(current_decrypted_referral_fund)

                    bonus_fund = float(500.00)
                    referral_bonus = current_decrypted_referral_fund - bonus_fund
                    MinimumBalance(referral_bonus)

                    encrypt_referral_fund = Cryptographer.encrypt(referral_bonus)
                    referral_wallet.fund = encrypt_referral_fund
                    referral_wallet.save()

                    user_wallet_to_delete = WalletModel.query.filter_by(user_id=new_user.id).first()
                    user_wallet_to_delete.delete()

                    user_to_delete = UserModel.query.filter_by(id=new_user.id).first()
                    user_to_delete.delete()

                    return jsonify({
                        'code': referral_response.status_code,
                        'code_status': referral_response.json().get('code_status', 'error'),
                        'message': referral_response.json().get('data', 'an error occurred registering referrals')
                    }), referral_response.status_code

            # KYC

            payload = {
                'user_id': str(new_user.id),
                'created_by_payverve': True,
                'email_address': new_user.email_address,
                'new_user': True,
            }

            kyc_response = requests.request("POST", f'{config.app_path}/kycs', json=payload)

            if kyc_response.status_code != 201:

                if referral_code:
                    ngn_wallet = CurrencyModel.query.filter_by(short_code='ngn').first().id
                    referral_wallet = WalletModel.query.filter_by(user_id=referral_confirmation_id,
                                                                  currency_id=ngn_wallet).first()

                    decrypted_referral_fund = Cryptographer.decrypt(referral_wallet.fund)
                    current_decrypted_referral_fund = float(decrypted_referral_fund)

                    MinimumBalance(current_decrypted_referral_fund)

                    bonus_fund = float(500.00)
                    referral_bonus = current_decrypted_referral_fund - bonus_fund
                    MinimumBalance(referral_bonus)

                    encrypt_referral_fund = Cryptographer.encrypt(referral_bonus)
                    referral_wallet.fund = encrypt_referral_fund
                    referral_wallet.save()

                user_wallet_to_delete = WalletModel.query.filter_by(user_id=new_user.id).first()
                user_wallet_to_delete.delete()

                user_to_delete = UserModel.query.filter_by(id=new_user.id).first()
                user_to_delete.delete()

                return jsonify({
                    'code': kyc_response.status_code,
                    'code_status': kyc_response.json().get('code_status', 'error'),
                    'message': kyc_response.json().get('data', 'an error occurred while creating wallet')
                }), kyc_response.status_code

            # send verification and welcome email

            # verification email

            verification_code = str(secrets.randbelow(1000000)).zfill(6)

            # noinspection PyArgumentList
            new_verification_code = TokenVerificationModel(
                channel='email',
                channel_contact=new_user.email_address,
                code_sent=Cryptographer.encrypt(verification_code),
                expiration_time=900,
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

            MailtrapHelper.mailtrap_email_sender(config.mailtrap_payverve_security_name,
                                                 config.mailtrap_payverve_security_email,
                                                 endpoint,
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

            MailtrapHelper.mailtrap_email_sender(config.mailtrap_payverve_eva_name,
                                                 config.mailtrap_payverve_eva_email,
                                                 endpoint,
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
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'message': str(e)
            }), 400

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'message': 'account already has an account'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
        }),

    @staticmethod
    def read_all():
        """ Retrieve all users account """

        users = UserModel.query.all()

        try:
            if not users:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no user account was found'
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
                    'deleted_date': user.deleted_date,
                    'email_verified': user.email_verified,
                    'account_active': user.account_active,
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
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
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
                    'message': 'no user account was found'
                }), 404

            data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'middle_name': user.middle_name,
                'username': user.username,
                'email_address': user.email_address,
                'mobile_number': user.mobile_number,
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
                'deleted_date': user.deleted_date,
                'email_verified': user.email_verified,
                'account_active': user.account_active,
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
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
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
        Argument("email_address", location="json"),
        Argument("mobile_number", location="json"),
        Argument("gender", location="json"),
        Argument("date_of_birth", location="json"),
        Argument("house_number", location="json"),
        Argument("street_name", location="json"),
        Argument("city", location="json"),
        Argument("state", location="json"),
        Argument("zipcode", location="json"),
        Argument("country", location="json"),
        Argument("photo", location="json"),
        Argument("username", location="json"),
    )
    def update(id=None, **fields):
        """ Updates a user account by id """

        user = UserModel.query.filter_by(id=id).first()

        try:
            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no user account was found'
                }), 404

            if 'first_name' in fields and fields['first_name'] is not None:
                user.first_name = fields['first_name']

            if 'last_name' in fields and fields['last_name'] is not None:
                user.last_name = fields['last_name']

            if 'middle_name' in fields and fields['middle_name'] is not None:
                user.middle_name = fields['middle_name']

            if 'email_address' in fields and fields['email_address'] is not None:
                user.email_address = fields['email_address']

            if 'mobile_number' in fields and fields['mobile_number'] is not None:
                user.mobile_number = fields['mobile_number']

            if 'gender' in fields and fields['gender'] is not None:

                gender_check = ["male", "female"]

                if fields['gender'].lower() not in gender_check:
                    return jsonify({
                        'code': 400,
                        'code_status': 'bad request',
                        'message': "gender must be either 'male' or 'female'"
                    }), 400

                user.gender = fields['gender']

            if 'date_of_birth' in fields and fields['date_of_birth'] is not None:

                parsed_date_of_birth = datetime.strptime(fields['date_of_birth'], '%Y-%m-%d').year
                age = int(datetime.now().year) - int(parsed_date_of_birth)

                if age < 17:
                    return jsonify({
                        'code': 400,
                        'code_status': 'bad request',
                        'message': 'you must be 17 years and above'
                    }), 400

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

            if 'username' in fields and fields['username'] is not None:
                user.username = fields['username']

            user.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "user account was successfully updated",
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
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
                    'message': 'no user account was found'
                }), 404

            if user.deleted:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'account is already staged for deleting'
                }), 400

            # user.deleted = True
            # user.deleted_date = datetime.now()
            # user.account_active = False
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
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

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
                    'message': 'verification code must be 6 digits'
                }), 400

            customer = UserModel.query.filter_by(email_address=email_address).first()

            if not customer:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'message': f'no account with {email_address} was found'
                }), 404

            if customer.email_verified:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'message': 'this user is already verified'
                }), 400

            confirmation = TokenVerificationModel.query.filter_by(
                channel="email",
                channel_contact=email_address,
            ).order_by(TokenVerificationModel.created_at.desc()).first()

            if not confirmation:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'message': 'verification code not found'
                }), 400

            confirmation_code = confirmation.code_sent
            decrypt_confirmation_code = Cryptographer.decrypt(confirmation_code)

            if not compare_digest(decrypt_confirmation_code, verification_code):
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'message': 'verification code does not match, try again'
                }), 400

            expected_expiry = confirmation.timestamp + timedelta(seconds=confirmation.expiration_time)

            if expected_expiry < datetime.now():
                confirmation.status = 'expired'
                confirmation.save()

                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': 'this code has expired'
                }), 403

            if confirmation.status == "verified":
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'message': 'this code has been verified'
                }), 400

            confirmation.status = 'verified'
            confirmation.save()

            customer.email_verified = True
            customer.account_active = True
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
                'message': f'an incorrect value was inputted: {str(e)}',
            }), 500

        except DataError:
            return jsonify({
                'code': 400,
                'code_message': 'bad request',
                'message': 'this error is a datatype error',
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
                    'message': 'this user is already verified'
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
                        'message': 'the previous code has not expire yet'
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
                expiration_time=900,
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

            MailtrapHelper.mailtrap_email_sender(config.mailtrap_payverve_security_name,
                                                 config.mailtrap_payverve_security_email,
                                                 endpoint,
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
                'message': f'an incorrect value was inputted: {str(e)}',
            }), 500

        except DataError:
            return jsonify({
                'code': 400,
                'code_message': 'bad request',
                'message': 'this error is a datatype error',
            }), 400

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "message": "this error is a database error",
            }), 500

    @staticmethod
    @parse_params(
        Argument("old_password", location="json", required=True),
        Argument("password", location="json", required=True),
    )
    def user_change_password(old_password: str, password: str, id=None):
        """ this method is used to change the password of a user """

        try:

            PasswordValidation(password)

            user = UserModel.query.filter_by(id=id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
                }), 404

            old_password_check = user.check_password(old_password)

            if not old_password_check:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old password is incorrect'
                }), 400

            if compare_digest(old_password, password):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old auth pin cannot be the same as the new auth pin'
                }), 400

            user.set_password(password)
            user.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "password changed successfully"
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'message': str(e)
            }), 400

    @staticmethod
    @parse_params(
        Argument("auth_pin", location="json", required=True, type=int),
    )
    def user_create_auth_pin(auth_pin, id=None):
        """ this method is used to create the auth pin of a user """

        try:

            if auth_pin is None or len(str(auth_pin)) != 6:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'auth pin must be a 6 digit number'
                }), 400

            if not isinstance(auth_pin, int):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'auth pin must be a number'
                }), 400

            user = UserModel.query.filter_by(id=id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no user account was found'
                }), 404

            auth_pin = str(auth_pin)

            user.set_auth_pin(auth_pin)
            user.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "Auth pin created successfully"
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'message': str(e)
            }), 400

    @staticmethod
    @parse_params(
        Argument("old_auth_pin", location="json", required=True, type=int),
        Argument("auth_pin", location="json", required=True, type=int),
    )
    def user_change_auth_pin(old_auth_pin, auth_pin, id=None):
        """ this method is used to change the auth pin of a user """

        try:

            if old_auth_pin is None or len(str(old_auth_pin)) != 6:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old auth pin must be a 6 digit number'
                }), 400

            if auth_pin is None or len(str(auth_pin)) != 6:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'auth pin must be a 6 digit number'
                }), 400

            if not isinstance(old_auth_pin, int):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old auth pin must be a number'
                }), 400

            if not isinstance(auth_pin, int):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'auth pin must be a number'
                }), 400

            user = UserModel.query.filter_by(id=id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no user account was found'
                }), 404

            check_pin = user.check_auth_pin(str(old_auth_pin))

            if not check_pin:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old auth pin is incorrect'
                }), 400

            if compare_digest(str(old_auth_pin), str(auth_pin)):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old auth pin cannot be the same as the new auth pin'
                }), 400

            auth_pin = str(auth_pin)

            user.set_auth_pin(auth_pin)
            user.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "auth pin changed successfully"
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'message': str(e)
            }), 400

    @staticmethod
    @parse_params(
        Argument("transaction_pin", location="json", required=True, type=int),
    )
    def user_create_transaction_pin(transaction_pin, id=None):
        """ this method is used to create the transaction_pin of a user """

        try:

            if transaction_pin is None or len(str(transaction_pin)) != 4:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'transaction pin must be a 4 digit number'
                }), 400

            if not isinstance(transaction_pin, int):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'transaction pin must be a number'
                }), 400

            user = UserModel.query.filter_by(id=id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no user account was found'
                }), 404

            user.set_transaction_pin(str(transaction_pin))
            user.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "Transaction pin created successfully"
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'message': str(e)
            }), 400

    @staticmethod
    @parse_params(
        Argument("old_transaction_pin", location="json", required=True, type=int),
        Argument("transaction_pin", location="json", required=True, type=int),
    )
    def user_change_transaction_pin(old_transaction_pin, transaction_pin, id=None):
        """ this method is used to change the transaction_pin of a user """

        try:

            if old_transaction_pin is None or len(str(old_transaction_pin)) != 4:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old transaction pin must be a 4 digit number'
                }), 400

            if transaction_pin is None or len(str(transaction_pin)) != 4:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'transaction pin must be a 4 digit number'
                }), 400

            if not isinstance(old_transaction_pin, int):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old transaction pin must be a number'
                }), 400

            if not isinstance(transaction_pin, int):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'transaction pin must be a number'
                }), 400

            user = UserModel.query.filter_by(id=id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no user account was found'
                }), 404

            old_transaction_pin_check = user.check_transaction_pin(old_transaction_pin)

            if not old_transaction_pin_check:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old transaction pin is incorrect'
                }), 400

            if compare_digest(str(old_transaction_pin), str(transaction_pin)):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'old transaction pin cannot be the same as the new transaction pin'
                }), 400

            user.set_transaction_pin(str(transaction_pin))
            user.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "transaction pin changed successfully"
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'message': str(e)
            }), 400

    @staticmethod
    @parse_params(
        Argument("transaction_pin", location="json", required=True, type=int),
    )
    def confirm_transaction_pin(transaction_pin, id=None):
        """  """

        try:

            if transaction_pin is None or len(str(transaction_pin)) != 4:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'transaction pin must be a 4 digit number'
                }), 400

            if not isinstance(transaction_pin, int):
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'transaction pin must be a number'
                }), 400

            user = UserModel.query.filter_by(id=id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no user account was found'
                }), 404

            if not user.transaction_pin:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'you do not have a transaction pin, create one'
                }), 400

            transaction_pin_check = user.check_transaction_pin(str(transaction_pin))

            if not transaction_pin_check:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'message': 'transaction pin is incorrect'
                }), 400

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "transaction pin is correct"
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'message': str(e)
            }), 400

        except TypeError as e:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - type error',
                'message': str(e)
            }), 400
