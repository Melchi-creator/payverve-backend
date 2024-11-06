"""
user.py

Defines all functions for users especially CRUD
"""
from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..middlewares import NetworkDateTime
from ..models import CurrencyModel, UserModel, WalletModel
from ..server import auth
from ..utilities import RandomGenerator, parse_params


class UserResource(Resource):
    """ This class is concern with User Resources """

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

        user_model = UserModel.query
        user_email = user_model.filter_by(email_address=email_address).first()
        user_number = user_model.filter_by(mobile_number=mobile_number).first()

        try:
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

            naira_currency = CurrencyModel.query.filter_by(short_code='ngn').first()

            # noinspection PyArgumentList
            new_wallet = WalletModel(
                fund=0,
                account_number=RandomGenerator.wallet_account_number(),
                user=new_user.id,
                currency=naira_currency.id
            )
            new_wallet.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'account was successfully created'
            }), 201

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

            if user.deleted is True:
                return jsonify({
                    'code': 400,
                    'code_status': 'bad request',
                    'data': 'account is already staged for deleting'
                }), 400

            user.deleted = True
            user.deleted_date = NetworkDateTime.network_datetime()
            user.save()

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


    @staticmethod
    @parse_params(
        Argument("email_address", location="json", required=True),
        Argument("password", location="json", required=True),
    )
    def login(email_address, password):
        """ Retrieve a user account by id """

        user = UserModel.query.filter_by(email_address=email_address).first()

        try:
            if not user:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no account was found'
                }), 404

            if user and user.check_password(password=password):
                return auth.login(user=user)

            return jsonify({
                'code': 401,
                'code_status': 'Invalid credentials',
            }), 401

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
    @auth.login_required
    def logout(**kwargs):
        """ Retrieve a user account by id """
        return auth.logout()


        