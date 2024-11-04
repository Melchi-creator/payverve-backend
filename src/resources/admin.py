"""
admin.py

Defines all functions for admin admins especially CRUD
"""
from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..middlewares import NetworkDateTime
from ..models import AdminModel, CurrencyModel, WalletModel
from ..utilities import RandomGenerator, parse_params

['id', 'first_name', 'last_name', 'middle_name', 'email_address', 'mobile_number', 'password', 'geneder', 'date_of_birth'
 'house_number', 'street_name', 'city', 'state', 'zipcode', 'country', 'photo', 'admin_role']

class AdminResource(Resource):
    """ This class is concern with admin Resources """

    @staticmethod
    @parse_params(
        Argument("first_name", location="json", required=True),
        Argument("last_name", location="json", required=True),
        Argument("email_address", location="json", required=True),
        Argument("mobile_number", location="json", required=True),
        Argument("password", location="json", required=True),
        Argument("gender", location="json", required=True),
        Argument("date_of_birth", location="json", required=True),
        Argument("admin_role", location="json", required=True)
    )
    def create(first_name, last_name, email_address, mobile_number, password, gender, date_of_birth, admin_role):
        """ Creates admins account """

        admin_model = AdminModel.query
        admin_email = admin_model.filter_by(email_address=email_address).first()
        admin_number = admin_model.filter_by(mobile_number=mobile_number).first()

        try:
            if admin_email:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'data': 'email address already has an account'
                }), 409

            if admin_number:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'data': 'mobile number already has an account'
                }), 409

            # noinspection PyArgumentList
            new_admin = AdminModel(
                first_name=first_name,
                last_name=last_name,
                email_address=email_address,
                mobile_number=mobile_number,
                gender=gender,
                date_of_birth=date_of_birth,
                admin_role=admin_role
            )
            new_admin.set_password(password)
            new_admin.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'admin account was successfully created'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'data': 'account already has an account'
            }), 409

        # except DataError:
        #     return jsonify({
        #         'code': 400,
        #         'code_status': 'bad request - data error',
        #         'data': 'ensure input data are correct'
        #     }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        # except (OperationalError, DisconnectionError, SQLAlchemyError):
        #     return jsonify({
        #         'code': 500,
        #         'code_status': 'database error - operation, sqlalchemy and disconnection error',
        #         'data': 'could not fetch data'
        #     }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all admins account """

        admins = AdminModel.query.all()

        try:
            if not admins:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no admin account was found'
                }), 404

            data = []

            for admin in admins:
                data.append({
                    'id': admin.id,
                    'first_name': admin.first_name,
                    'last_name': admin.last_name,
                    'middle_name': admin.middle_name,
                    'email_address': admin.email_address,
                    'mobile_number': admin.mobile_number,
                    'password': admin.password,
                    'gender': admin.gender,
                    'date_of_birth': admin.date_of_birth,
                    'house_number': admin.house_number,
                    'street_name': admin.street_name,
                    'city': admin.city,
                    'state': admin.state,
                    'zipcode': admin.zipcode,
                    'country': admin.country,
                    'photo': admin.photo,
                    'admin_role': admin.admin_role
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
        """ Retrieve a admin account by id """

        admin = AdminModel.query.filter_by(id=id).first()

        try:
            if not admin:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no admin account was found'
                }), 404

            data = {
                'id': admin.id,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'middle_name': admin.middle_name,
                'email_address': admin.email_address,
                'mobile_number': admin.mobile_number,
                'password': admin.password,
                'gender': admin.gender,
                'date_of_birth': admin.date_of_birth,
                'house_number': admin.house_number,
                'street_name': admin.street_name,
                'city': admin.city,
                'state': admin.state,
                'zipcode': admin.zipcode,
                'country': admin.country,
                'photo': admin.photo,
                'admin_role': admin.admin_role,
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
        Argument("email_address", location="json"),
        Argument("mobile_number", location="json"),
        Argument("password", location="json"),
        Argument("gender", location="json"),
        Argument("date_of_birth", location="json"),
        Argument("house_number", location="json"),
        Argument("street_name", location="json"),
        Argument("city", location="json"),
        Argument("state", location="json"),
        Argument("zipcode", location="json"),
        Argument("country", location="json"),
        Argument("photo", location="json"),
        Argument("admin_role", location="json"),
    )
    def update(id=None, **fields):
        """ Updates a admin account by id """

        admin = AdminModel.query.filter_by(id=id).first()

        try:
            if not admin:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no admin account was found'
                }), 404
                
            for (key, value) in fields.items():
                if value is not None:
                    setattr(admin, key, value)

            # if 'first_name' in fields and fields['first_name'] is not None:
            #     admin.first_name = fields['first_name']

            # if 'last_name' in fields and fields['last_name'] is not None:
            #     admin.last_name = fields['last_name']

            # if 'middle_name' in fields and fields['middle_name'] is not None:
            #     admin.middle_name = fields['middle_name']

            # if 'adminname' in fields and fields['adminname'] is not None:
            #     admin.adminname = fields['adminname']

            # if 'email_address' in fields and fields['email_address'] is not None:
            #     admin.email_address = fields['email_address']

            # if 'mobile_number' in fields and fields['mobile_number'] is not None:
            #     admin.mobile_number = fields['mobile_number']

            # if 'password' in fields and fields['password'] is not None:
            #     admin.set_password(fields['password'])

            # if 'auth_pin' in fields and fields['auth_pin'] is not None:
            #     admin.set_auth_pin(fields['auth_pin'])

            # if 'transaction_pin' in fields and fields['transaction_pin'] is not None:
            #     admin.set_transaction_pin(fields['transaction_pin'])

            # if 'gender' in fields and fields['gender'] is not None:
            #     admin.gender = fields['gender']

            # if 'date_of_birth' in fields and fields['date_of_birth'] is not None:
            #     admin.date_of_birth = fields['date_of_birth']

            # if 'house_number' in fields and fields['house_number'] is not None:
            #     admin.house_number = fields['house_number']

            # if 'street_name' in fields and fields['street_name'] is not None:
            #     admin.street_name = fields['street_name']

            # if 'city' in fields and fields['city'] is not None:
            #     admin.city = fields['city']

            # if 'state' in fields and fields['state'] is not None:
            #     admin.state = fields['state']

            # if 'zipcode' in fields and fields['zipcode'] is not None:
            #     admin.zipcode = fields['zipcode']

            # if 'country' in fields and fields['country'] is not None:
            #     admin.country = fields['country']
    
            # if 'photo' in fields and fields['photo'] is not None:
            #     admin.photo = fields['photo']

            # if 'deleted' in fields and fields['deleted'] is not None:
            #     admin.deleted = fields['deleted']

            admin.save()

            data = {
                'id': admin.id,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'middle_name': admin.middle_name,
                'email_address': admin.email_address,
                'mobile_number': admin.mobile_number,
                'password': admin.password,
                'gender': admin.gender,
                'date_of_birth': admin.date_of_birth,
                'house_number': admin.house_number,
                'street_name': admin.street_name,
                'city': admin.city,
                'state': admin.state,
                'zipcode': admin.zipcode,
                'country': admin.country,
                'photo': admin.photo,
                'admin_role': admin.admin_role,
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
        """ Retrieve and delete a admin account by id """

        admin = AdminModel.query.filter_by(id=id).first()

        try:
            if not admin:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no admin account was found'
                }), 404

            admin.delete()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'admin ccount has been deleted'
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


