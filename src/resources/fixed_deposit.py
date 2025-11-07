"""

"""
import secrets
from datetime import datetime, timedelta
from hmac import compare_digest

from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from psycopg2 import DataError, IntegrityError, InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DisconnectionError, SQLAlchemyError

from ..models import CurrencyModel, FixedDepositModel, TransactionModel, WalletModel
from ..utilities import Cryptographer, parse_params
from ..value_object import MinimumBalance


class FixedDepositResource(Resource):
    """ """

    @staticmethod
    @parse_params(
        Argument("target_amount", location="json", required=True),
        Argument("duration", type=int, location="json", required=True),
        Argument("user_id", location="json", required=True),
    )
    def create(target_amount, duration, user_id):
        """ """

        try:

            title = secrets.token_urlsafe(16)

            if not compare_digest(str(duration), '3') and not compare_digest(str(duration), '6') and not compare_digest(
                    str(duration),
                    '12'):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'duration must be either 3, 6 or 12 months',
                }), 400

            ngn_wallet = WalletModel.query.filter_by(user_id=user_id, currency_ticker='ngn').first()
            decrypt_balance = Cryptographer.decrypt(ngn_wallet.fund)

            end_date = None

            if compare_digest(str(duration), '3'):
                end_date = datetime.now() + timedelta(days=90)

            if compare_digest(str(duration), '6'):
                end_date = datetime.now() + timedelta(days=180)

            if compare_digest(str(duration), '12'):
                end_date = datetime.now() + timedelta(days=365)

            if float(decrypt_balance) < float(target_amount):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'your wallet balance is too low, try again later',
                }), 400

            balance = Cryptographer.encrypt(target_amount)

            # noinspection PyArgumentList
            new_fixed_deposit = FixedDepositModel(
                balance=balance,
                title=title,
                user_id=user_id,
                target_amount=target_amount,
                duration=duration,
                end_date=end_date,
                start_date=datetime.now(),
            )

            new_fixed_deposit.save()

            wallet_final_balance = float(decrypt_balance) - float(target_amount)
            MinimumBalance(wallet_final_balance)
            ngn_wallet.fund = Cryptographer.encrypt(wallet_final_balance)
            ngn_wallet.save()

            currency_id = CurrencyModel.query.filter_by(short_code='ngn').first().id

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=Cryptographer.encrypt(target_amount),
                transaction_type='fixed_deposit',
                user_id=user_id,
                currency_id=currency_id,
                note=f"₦{float(target_amount):,} has been saved in your fixed deposit -> {title}",
                status='successful'
            )

            new_transaction.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'your target saving has been created successfully',
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
    def read():
        """ """

        try:

            fixed_deposits = FixedDepositModel.query.all()

            if not fixed_deposits:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'fixed deposits not found'
                }), 404

            data = [
                {
                    'id': fd.id,
                    'balance': Cryptographer.decrypt(fd.balance),
                    'target_amount': fd.target_amount,
                    'duration': fd.duration,
                    'title': fd.title,
                    'is_active': fd.is_active,
                    'end_date': fd.end_date,
                    'start_date': fd.start_date,
                    'is_deleted': fd.is_deleted,
                    'deleted_at': fd.deleted_at,
                    'created_at': fd.created_at,
                    'updated_at': fd.updated_at,
                    'user_id': fd.user_id,
                    'user': fd.users.first_name + ' ' + fd.users.last_name,
                }
                for fd in fixed_deposits
            ]

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
    def fetch(id=None):
        """ """

        try:

            fixed_deposit = FixedDepositModel.query.filter_by(id=id).first()

            if not fixed_deposit:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'fixed deposits not found'
                }), 404

            data = {
                'id': fixed_deposit.id,
                'balance': Cryptographer.decrypt(fixed_deposit.balance),
                'target_amount': fixed_deposit.target_amount,
                'duration': fixed_deposit.duration,
                'title': fixed_deposit.title,
                'is_active': fixed_deposit.is_active,
                'end_date': fixed_deposit.end_date,
                'start_date': fixed_deposit.start_date,
                'is_deleted': fixed_deposit.is_deleted,
                'deleted_at': fixed_deposit.deleted_at,
                'created_at': fixed_deposit.created_at,
                'updated_at': fixed_deposit.updated_at,
                'user_id': fixed_deposit.user_id,
                'user': fixed_deposit.users.first_name + ' ' + fixed_deposit.users.last_name,
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
    def fetch_user_fd(id=None):
        """ """

        try:

            fixed_deposits = FixedDepositModel.query.filter_by(user_id=id).all()

            if not fixed_deposits:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'fixed deposits not found'
                }), 404

            data = [
                {
                    'id': fd.id,
                    'balance': Cryptographer.decrypt(fd.balance),
                    'target_amount': fd.target_amount,
                    'duration': fd.duration,
                    'title': fd.title,
                    'is_active': fd.is_active,
                    'end_date': fd.end_date,
                    'start_date': fd.start_date,
                    'is_deleted': fd.is_deleted,
                    'deleted_at': fd.deleted_at,
                    'created_at': fd.created_at,
                    'updated_at': fd.updated_at,
                    'user_id': fd.user_id,
                    'user': fd.users.first_name + ' ' + fd.users.last_name,
                }
                for fd in fixed_deposits
            ]

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
    def withdraw_fixed_deposit(id=None, user_id=None):
        """ """

        try:

            fixed_deposits = FixedDepositModel.query.filter_by(user_id=user_id, id=id, is_active=False).first()

            if not fixed_deposits:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'target savings not found or still active'
                }), 404

            if fixed_deposits.is_deleted:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'target saving already deleted'
                }), 400

            if fixed_deposits.is_active:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you can only withdraw from an inactive target saving'
                }), 400

            if not fixed_deposits.is_active and fixed_deposits.end_date > datetime.now():
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you can only withdraw from matured fixed deposits'
                }), 400

            decrypt_balance = Cryptographer.decrypt(fixed_deposits.balance)

            wallet = WalletModel.query.filter_by(user_id=user_id, currency_ticker='ngn').first()

            decrypt_wallet_balance = Cryptographer.decrypt(wallet.fund)
            final_balance = float(decrypt_wallet_balance) + float(decrypt_balance)
            MinimumBalance(final_balance)

            wallet.fund = Cryptographer.encrypt(final_balance)
            wallet.save()

            fixed_deposits.is_deleted = True
            fixed_deposits.deleted_at = datetime.now()
            fixed_deposits.balance = Cryptographer.encrypt(0)
            fixed_deposits.save()

            currency_id = CurrencyModel.query.filter_by(short_code='ngn').first().id

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=Cryptographer.encrypt(decrypt_balance),
                transaction_type='fixed_deposit_withdrawal',
                user_id=user_id,
                currency_id=currency_id,
                note=f"₦{float(decrypt_balance):,} has been withdrawn from your fixed deposit -> {fixed_deposits.title}",
                status='successful'
            )

            new_transaction.save()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'target savings withdrawal was successful'
            })

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


    # @ TODO: background worker for automated interest accumulation
