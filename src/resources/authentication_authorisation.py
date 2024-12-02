"""authentication_authorisation.py

Keyword arguments:
argument -- description
Return: return_description
"""

from flask.json import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, SQLAlchemyError

from ..models import AdminModel, UserModel
from ..utilities import parse_params


# OopCompanion:suppressRename


class AuthResource(Resource):
    """ The class defines the auth resources  """

    # Admin

    @staticmethod
    @parse_params(
        Argument("email_address", location="json",
                 help="The email address of the business"),
        Argument("mobile_number", location="json",
                 help="The mobile number of the business"),
        Argument("password", location="json", required=True,
                 help="The password of the business"),
    )
    def admin_login(email_address, mobile_number, password):
        """ this function defines the admin auth """

        try:
            user_email_address = AdminModel.query.filter_by(email_address=email_address).first()
            user_mobile_number = AdminModel.query.filter_by(mobile_number=mobile_number).first()

            user_account = None

            if not email_address and not mobile_number:
                return jsonify({
                    "code": 409,
                    "code_status": "bad request",
                    "data": "check your request email_address or mobile_number key is missing."
                }), 409

            if email_address and user_email_address:
                user_account = user_email_address

            if email_address and not user_account:
                return jsonify({
                    "code": 404,
                    "code_status": "Not Found",
                    "data": f"the account you are trying to access with {email_address} was not found."
                }), 404

            if mobile_number and user_mobile_number:
                user_account = user_mobile_number

            if mobile_number and not user_account:
                return jsonify({
                    "code": 404,
                    "code_status": "not found",
                    "data": f"the account you are trying to access with {mobile_number} was not found."
                }), 404

            user_password = user_account.check_password(password)

            if not user_password:
                return jsonify({
                    "code": 401,
                    "code_status": "incorrect password",
                }), 401

            # if user_account.email_verified is False:
            #     return jsonify({
            #         "code": 401,
            #         "code_status": "your account with us is not verified",
            #     }), 401

            if user_account:
                if user_password:
                    return jsonify({
                        "code": 200,
                        'code_status': 'success',
                        'data': f'Successfully logged in.',
                        'data_details': {
                            'id': user_account.id,
                            'first_name': user_account.first_name,
                            'last_name': user_account.last_name,
                            'phone_number': user_account.mobile_number,
                            'email_address': user_account.email_address,
                            'created_at': user_account.created_at,
                            'updated_at': user_account.updated_at
                        }
                    }), 200

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

    # Customer

    @staticmethod
    @parse_params(
        Argument("email_address", location="json",
                 help="The email address of the business"),
        Argument("mobile_number", location="json",
                 help="The mobile number of the business"),
        Argument("password", location="json", required=True,
                 help="The password of the business"),
    )
    def user_login(email_address, mobile_number, password):
        """ this function defines the admin auth """

        try:
            user_email_address = UserModel.query.filter_by(email_address=email_address).first()
            user_mobile_number = UserModel.query.filter_by(mobile_number=mobile_number).first()

            user_account = None

            if not email_address and not mobile_number:
                return jsonify({
                    "code": 409,
                    "code_status": "bad request",
                    "data": "check your request email_address or mobile_number key is missing."
                }), 409

            if email_address and user_email_address:
                user_account = user_email_address

            if email_address and not user_account:
                return jsonify({
                    "code": 404,
                    "code_status": "Not Found",
                    "data": f"the account you are trying to access with {email_address} was not found."
                }), 404

            if mobile_number and user_mobile_number:
                user_account = user_mobile_number

            if mobile_number and not user_account:
                return jsonify({
                    "code": 404,
                    "code_status": "Not Found",
                    "data": f"the account you are trying to access with {mobile_number} was not found."
                }), 404

            user_password = user_account.check_password(password)

            if not user_password:
                return jsonify({
                    "code": 401,
                    "code_status": "incorrect password",
                }), 401

            # if user_account.email_verified is False:
            #     return jsonify({
            #         "code": 401,
            #         "code_status": "your account with us is not verified",
            #     }), 401

            if user_account:
                if user_password:
                    return jsonify({
                        "code": 200,
                        'code_status': 'success',
                        'data': f'successfully logged in.',
                        'data_details': {
                            'id': user_account.id,
                            'first_name': user_account.first_name,
                            'last_name': user_account.last_name,
                            'phone_number': user_account.mobile_number,
                            'email_address': user_account.email_address,
                            'created_at': user_account.created_at,
                            'updated_at': user_account.updated_at
                        }
                    }), 200

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
