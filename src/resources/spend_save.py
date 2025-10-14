"""
src/resources/payverve_transfer.py
This module defines the PayverveTransferResource class, which handles Payverve transfer operations.
It includes methods for creating, reading, and deleting Payverve transfers, with error handling for
various database and validation errors.
"""

from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, SQLAlchemyError

from ..models import SpendSaveModel, UserModel
from ..utilities import Cryptographer, parse_params


class SpendSaveResource(Resource):
    """  """

    @staticmethod
    @parse_params(
        Argument("percentage_to_save", location="json", required=True),
        Argument("user_id", location="json", required=True),
    )
    def create(percentage_to_save, user_id):
        """ """

        try:

            confirm_user = UserModel.query.filter_by(id=user_id).first()

            if not confirm_user:
                return jsonify({
                    'code': 404,
                    'message': 'not found',
                    'data': 'user not found',
                }), 404

            already_setup = SpendSaveModel.query.filter_by(user_id=user_id).first()

            if already_setup:
                return jsonify({
                    'code': 409,
                    'message': 'user already setup',
                    'data': 'spend and save already setup, please update instead',
                })

            initial_balance = Cryptographer.encrypt(float(0))

            # noinspection PyArgumentList
            new_spend_save = SpendSaveModel(
                percentage_to_save=percentage_to_save,
                user_id=user_id,
                balance=initial_balance,
            )

            new_spend_save.save()

            return jsonify({
                'code': 201,
                'message': 'created',
                'data': 'spend and send successfully setup'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'message': 'conflict - integrity error',
                'data': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'message': 'bad request - data error',
                'data': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'message': 'calculation error - arithmetic, value, zerodivision error',
                'data': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all payverve transfer """

        spend_saves = SpendSaveModel.query.order_by(SpendSaveModel.created_at.desc()).all()

        try:
            if not spend_saves:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'no spend and save found'
                }), 404

            data = []

            for spend_save in spend_saves:
                data.append({
                    'id': spend_save.id,
                    'balance': Cryptographer.decrypt(spend_save.balance),
                    'percentage_to_save': spend_save.percentage_to_save,
                    'is_active': spend_save.is_active,
                    'user_id': spend_save.user_id,
                    'user': spend_save.users.first_name + ' ' + spend_save.users.last_name,
                    'created_at': spend_save.created_at,
                    'updated_at': spend_save.updated_at
                })

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """ Retrieve one payverve transfer by id """

        spend_save = SpendSaveModel.query.filter_by(user_id=id).first()

        try:
            if not spend_save:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'no spend and save was found'
                }), 404

            data = {
                'id': spend_save.id,
                'balance': Cryptographer.decrypt(spend_save.balance),
                'percentage_to_save': spend_save.percentage_to_save,
                'is_active': spend_save.is_active,
                'user_id': spend_save.user_id,
                'user': spend_save.users.first_name + ' ' + spend_save.users.last_name,
                'created_at': spend_save.created_at,
                'updated_at': spend_save.updated_at
            }

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    @parse_params(
        Argument('percentage_to_save', type=int, location='json'),
        Argument('is_active', location='json'),
    )
    def update(id=None, **fields):
        """ Update a wallet's fund """

        try:

            spend_save = SpendSaveModel.query.filter_by(user_id=id).first()

            if not spend_save:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'user doesn\'t have spend and save setup'
                }), 404

            if 'percentage_to_save' in fields and fields['percentage_to_save'] is not None:
                spend_save.percentage_to_save = int(fields['percentage_to_save'])

            if 'is_active' in fields and fields['is_active'] is not None:
                spend_save.is_active = fields['is_active']

            spend_save.save()

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': 'spend and save was successfully updated'
            }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'message': 'conflict - integrity error',
                'data': 'a wallet with this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'message': 'bad request - data error',
                'data': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    @parse_params(
        Argument("amount", location="json", required=True),
    )
    def withdraw_spend_save(amount, id=None):
        """ """

        try:

            confirm_user = SpendSaveModel.query.filter_by(user_id=id).first()

            if not confirm_user:
                return jsonify({
                    'code': 404,
                    'message': 'not found',
                    'data': 'user not found',
                }), 404

            decrypt_balance = Cryptographer.decrypt(confirm_user.balance)

            if float(amount) > float(decrypt_balance):
                return jsonify({
                    'code': 400,
                    'message': 'bad request',
                    'data': f'amount too high, you have {decrypt_balance} as you balance',
                }), 400

            final_balance = float(decrypt_balance) - float(amount)

            if final_balance < 0:
                return jsonify({
                    'code': 400,
                    'message': 'bad request',
                    'data': f'amount too low, you {decrypt_balance} as you balance',
                }), 400

            encrypt_balance = Cryptographer.encrypt(final_balance)
            confirm_user.balance = encrypt_balance
            confirm_user.save()

            return jsonify({
                'code': 201,
                'message': 'created',
                'data': 'Withdrawal was successful from your spend and send'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'message': 'conflict - integrity error',
                'data': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'message': 'bad request - data error',
                'data': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'message': 'calculation error - arithmetic, value, zerodivision error',
                'data': 'could run an arithmetic calculation'
            }), 500
