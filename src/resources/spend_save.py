"""
src/resources/payverve_transfer.py
This module defines the PayverveTransferResource class, which handles Payverve transfer operations.
It includes methods for creating, reading, and deleting Payverve transfers, with error handling for
various database and validation errors.
"""
from hmac import compare_digest

from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, SQLAlchemyError

from . import NotificationResource
from ..models import CurrencyModel, SpendSaveModel, TransactionModel, UserModel, WalletModel
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
                    'status_message': 'not found',
                    'message': 'user not found',
                }), 404

            already_setup = SpendSaveModel.query.filter_by(user_id=user_id).first()

            if already_setup:
                return jsonify({
                    'code': 409,
                    'status_message': 'user already setup',
                    'message': 'spend and save already setup, please update percentage instead or turn it on if off',
                })

            initial_balance = Cryptographer.encrypt(float(0))

            # noinspection PyArgumentList
            new_spend_save = SpendSaveModel(
                percentage_to_save=percentage_to_save,
                user_id=user_id,
                balance=initial_balance,
            )

            new_spend_save.save()

            NotificationResource.store_nofication(
                title="Spend and Save",
                body=f"Spend and save has been successfully setup with {percentage_to_save}% to save",
                user_id=id,
            )

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'spend and send successfully setup'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'status_message': 'calculation error - arithmetic, value, zerodivision error',
                'message': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all payverve transfer """

        spend_saves = SpendSaveModel.query.order_by(SpendSaveModel.created_at.desc()).all()

        try:
            if not spend_saves:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no spend and save found'
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
                'status_message': 'success',
                'data': data
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

    @staticmethod
    def read_one(id=None):
        """ Retrieve one payverve transfer by id """

        spend_save = SpendSaveModel.query.filter_by(user_id=id).first()

        try:
            if not spend_save:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no spend and save was found'
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
                'status_message': 'success',
                'data': data
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

    @staticmethod
    @parse_params(
        Argument('percentage_to_save', type=int, location='json', required=True),
    )
    def update_percentage(id=None, **fields):
        """ Update a wallet's fund """

        try:

            spend_save = SpendSaveModel.query.filter_by(user_id=id).first()

            if not spend_save:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'user doesn\'t have spend and save setup'
                }), 404

            if 'percentage_to_save' in fields and fields['percentage_to_save'] is not None:
                spend_save.percentage_to_save = int(fields['percentage_to_save'])

            spend_save.save()

            NotificationResource.store_nofication(
                title="Spend and Save",
                body=f"Your spend and save percentage has been updated to {fields['percentage_to_save']}%",
                user_id=id,
            )

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'spend and save percentage was successfully updated'
            }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'a wallet with this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }),

    @staticmethod
    @parse_params(
        Argument('is_active', location='json', type=bool, required=True),
    )
    def toggle_spend_save(id=None, **fields):
        """ Update a wallet's fund """

        try:

            spend_save = SpendSaveModel.query.filter_by(user_id=id).first()

            if not spend_save:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'user doesn\'t have spend and save setup'
                }), 404

            if compare_digest(str(fields['is_active']).lower(), 'true') and str(spend_save.is_active).lower() == 'true':
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'spend and save is already active'
                }), 400

            if compare_digest(str(fields['is_active']).lower(),
                              'false') and str(spend_save.is_active).lower() == 'false':
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'spend and save is already inactive'
                }), 400

            if 'is_active' in fields and fields['is_active'] is not None:
                spend_save.is_active = fields['is_active']

            spend_save.save()

            NotificationResource.store_nofication(
                title="Spend and Save",
                body=f"Your spend and save has been {'enabled' if compare_digest(str(fields['is_active']).lower(), 'true') else 'disabled'}",
                user_id=id,
            )

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': f'spend and save has be {'enabled' if compare_digest(str(fields['is_active']).lower(), 'true') else 'disabled'} successfully'
            }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'a wallet with this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
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
                    'status_message': 'not found',
                    'message': 'user not found',
                }), 404

            decrypt_balance = Cryptographer.decrypt(confirm_user.balance)

            if float(amount) > float(decrypt_balance):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': f'amount too high, you have {decrypt_balance} as you balance',
                }), 400

            final_balance = float(decrypt_balance) - float(amount)

            if final_balance < 0:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': f'amount too low, you {decrypt_balance} as you balance',
                }), 400

            encrypt_balance = Cryptographer.encrypt(final_balance)
            confirm_user.balance = encrypt_balance
            confirm_user.save()

            user_wallet = WalletModel.query.filter_by(user_id=id, currency_ticker='ngn').first()

            if not user_wallet:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': f'wallet to fund not found',
                }), 404

            decrypt_wallet_balance = Cryptographer.decrypt(user_wallet.fund)
            final_wallet_balance = float(decrypt_wallet_balance) + float(amount)
            encrypt_wallet_balance = Cryptographer.encrypt(final_wallet_balance)

            user_wallet.fund = encrypt_wallet_balance
            user_wallet.save()

            currency_id = CurrencyModel.query.filter_by(short_code='ngn').first().id

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=Cryptographer.encrypt(amount),
                transaction_type='spend_and_save_withdrawal',
                user_id=id,
                currency_id=currency_id,
                note=f'{amount} NGN was withdrawn from spend and save to wallet',
                status='successful',
                name=f'{user_wallet.users.first_name} {user_wallet.users.last_name}',
                transaction_flow='debit',
                transaction_title='Money Withdrawn',
                currency_ticker='ngn',
            )
            new_transaction.save()

            NotificationResource.store_nofication(
                title="Spend and Save Withdrawal",
                body=f"₦{float(decrypt_balance):,} has been withdrawn from your Spend and Save",
                user_id=id,
            )

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'Withdrawal was successful from your spend and send'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'status_message': 'calculation error - arithmetic, value, zerodivision error',
                'message': 'could run an arithmetic calculation'
            }), 500

