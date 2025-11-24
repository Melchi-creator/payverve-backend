"""

"""
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from hmac import compare_digest

from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from psycopg2 import DataError, IntegrityError, InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DisconnectionError, SQLAlchemyError

from .notification import NotificationResource
from ..models import CurrencyModel, TargetSaveModel, TransactionModel, WalletModel
from ..utilities import Cryptographer, parse_params
from ..value_object import MinimumBalance


class TargetSaveResource(Resource):
    """ """

    @staticmethod
    @parse_params(
        Argument("target_amount", location="json", required=True),
        Argument("end_date", location="json", required=True),
        Argument("interval", location="json", required=True),
        Argument("title", location="json", required=True),
        Argument("user_id", location="json", required=True),
    )
    def create(target_amount, end_date, interval, title, user_id):
        """ """

        try:

            existing_ts = TargetSaveModel.query.filter_by(title=title.lower()).first()

            if existing_ts:
                if SequenceMatcher(None, str(existing_ts.title.lower()), str(title.lower())).ratio() > 0.4:
                    return jsonify({
                        'code': 409,
                        'status_message': 'conflict',
                        'message': f'a similar target saving with title {existing_ts.title} already exists',
                    }), 409

            if not compare_digest(str(interval.lower()), "hourly") and not compare_digest(str(interval.lower()),
                                                                                          "daily") and not compare_digest(
                str(
                    interval.lower()),
                "weekly") and not compare_digest(str(interval.lower()), "monthly"):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'intervals must be either hourly or daily or weekly or monthly',
                }), 400

            ngn_wallet = WalletModel.query.filter_by(user_id=user_id, currency_ticker='ngn').first()
            decrypt_balance = Cryptographer.decrypt(ngn_wallet.fund)

            if float(decrypt_balance) < float(target_amount):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'your wallet balance is too low, try again later',
                }), 400

            next_saving = None

            if compare_digest(str(interval.lower()), "hourly"):
                next_saving = datetime.now() + timedelta(hours=1)

            if compare_digest(str(interval.lower()), "daily"):
                next_saving = datetime.now() + timedelta(days=1)

            if compare_digest(str(interval.lower()), "weekly"):
                next_saving = datetime.now() + timedelta(weeks=1)

            if compare_digest(str(interval.lower()), "monthly"):
                next_saving = datetime.now() + timedelta(days=30)

            balance = Cryptographer.encrypt(target_amount)

            # noinspection PyArgumentList
            new_target_save = TargetSaveModel(
                balance=balance,
                title=title.lower(),
                user_id=user_id,
                target_amount=target_amount,
                interval=interval.lower(),
                next_saving=next_saving,
                end_date=end_date,
                last_attempted_saving=datetime.now(),
                start_date=datetime.now(),
            )

            new_target_save.save()

            wallet_final_balance = float(decrypt_balance) - float(target_amount)
            MinimumBalance(wallet_final_balance)
            ngn_wallet.fund = Cryptographer.encrypt(wallet_final_balance)
            ngn_wallet.save()

            currency_id = CurrencyModel.query.filter_by(short_code='ngn').first().id

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=Cryptographer.encrypt(target_amount),
                transaction_type='target_save',
                user_id=user_id,
                currency_id=currency_id,
                note=f"₦{float(target_amount):,} has been saved in your target saving {title.lower()}",
                status='successful',
                name=f'{ngn_wallet.users.first_name} {ngn_wallet.users.last_name}',
                transaction_flow='debit',
                transaction_title='Money Saved',
                currency_ticker=ngn_wallet.currency_ticker,
            )

            new_transaction.save()

            NotificationResource.store_nofication(
                title="Target Saving Created",
                body=f"₦{float(target_amount):,.2f} has been saved in your target saving {title.lower()}",
                user_id=user_id,
            )

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
    def human_duration(start, end):
        days = (end - start).days

        if days < 7:
            return f"{days} days"

        weeks = days // 7
        if weeks < 4:
            return f"{weeks} weeks"

        months = days // 30  # rough but practical for product usage
        return f"{months} months"

    @staticmethod
    def read():
        """ """

        try:

            target_savings = TargetSaveModel.query.all()

            if not target_savings:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'target savings not found'
                }), 404

            data = [
                {
                    'id': ts.id,
                    'balance': Cryptographer.decrypt(ts.balance),
                    'target_amount': ts.target_amount,
                    'interval': ts.interval,
                    'title': ts.title,
                    'is_active': ts.is_active,
                    'last_successful_saving': ts.last_successful_saving,
                    'last_attempted_saving': ts.last_attempted_saving,
                    'next_saving': ts.next_saving,
                    'end_date': ts.end_date,
                    'start_date': ts.start_date,
                    'duration': TargetSaveResource.human_duration(ts.start_date, ts.end_date),
                    'created_at': ts.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': ts.updated_at.strftime("%d %b %Y, %I:%M %p") if ts.updated_at else None,
                    'user_id': ts.user_id,
                    'user': ts.users.first_name + ' ' + ts.users.last_name,
                    'is_deleted': ts.is_deleted,
                    'deleted_at': ts.deleted_at.strftime("%d %b %Y, %I:%M %p") if ts.updated_at else None,
                }
                for ts in target_savings
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

            target_saving = TargetSaveModel.query.filter_by(id=id).first()

            if not target_saving:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'target savings not found'
                }), 404

            data = {
                'id': target_saving.id,
                'balance': Cryptographer.decrypt(target_saving.balance),
                'target_amount': target_saving.target_amount,
                'interval': target_saving.interval,
                'title': target_saving.title,
                'is_active': target_saving.is_active,
                'last_successful_saving': target_saving.last_successful_saving,
                'last_attempted_saving': target_saving.last_attempted_saving,
                'next_saving': target_saving.next_saving,
                'end_date': target_saving.end_date,
                'start_date': target_saving.start_date,
                'duration': TargetSaveResource.human_duration(target_saving.start_date, target_saving.end_date),
                'created_at': target_saving.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': target_saving.updated_at.strftime("%d %b %Y, %I:%M %p") if target_saving.updated_at else None,
                'user_id': target_saving.user_id,
                'user': target_saving.users.first_name + ' ' + target_saving.users.last_name,
                'is_deleted': target_saving.is_deleted,
                'deleted_at': target_saving.deleted_at.strftime("%d %b %Y, %I:%M %p") if target_saving.updated_at else None,
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
    def fetch_user_ts(id=None):
        """ """

        try:

            target_savings = TargetSaveModel.query.filter_by(user_id=id).all()

            if not target_savings:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'target savings not found'
                }), 404

            data = [
                {
                    'id': ts.id,
                    'balance': Cryptographer.decrypt(ts.balance),
                    'target_amount': ts.target_amount,
                    'interval': ts.interval,
                    'title': ts.title,
                    'is_active': ts.is_active,
                    'last_successful_saving': ts.last_successful_saving,
                    'last_attempted_saving': ts.last_attempted_saving,
                    'next_saving': ts.next_saving,
                    'end_date': ts.end_date,
                    'start_date': ts.start_date,
                    'duration': TargetSaveResource.human_duration(ts.start_date, ts.end_date),
                    'created_at': ts.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': ts.updated_at.strftime("%d %b %Y, %I:%M %p") if ts.updated_at else None,
                    'user_id': ts.user_id,
                    'user': ts.users.first_name + ' ' + ts.users.last_name,
                    'is_deleted': ts.is_deleted,
                    'deleted_at': ts.deleted_at.strftime("%d %b %Y, %I:%M %p") if ts.updated_at else None
                }
                for ts in target_savings
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
    def break_ts(id=None, user_id=None):
        """ """

        try:

            target_savings = TargetSaveModel.query.filter_by(user_id=user_id, id=id, is_active=True).first()

            if not target_savings:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'target savings not found or it\'s inactive'
                }), 404

            if target_savings.is_deleted:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'target saving already deleted'
                }), 400

            if datetime.now() > target_savings.end_date - timedelta(days=30):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you can only break a saving if it matures in less than 30 days'
                }), 400

            target_savings.is_active = False
            target_savings.save()

            NotificationResource.store_nofication(
                title="Target Saving Break",
                body=f"You have unlocked your target savings -> {target_savings.title}",
                user_id=user_id,
            )

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'target savings has been successfully broken and is now inactive'
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
    @parse_params(
        Argument("target_amount", location="json", required=True),
    )
    def withdraw_target_saving(target_amount, id=None, user_id=None):
        """ """

        try:

            target_savings = TargetSaveModel.query.filter_by(user_id=user_id, id=id, is_active=False).first()

            if not target_savings:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'target savings not found or still active'
                }), 404

            if target_savings.is_deleted:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'target saving already deleted'
                }), 400

            if target_savings.is_active:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you can only withdraw from an inactive target saving'
                }), 400

            decrypt_balance = Cryptographer.decrypt(target_savings.balance)

            if float(target_amount) > float(decrypt_balance):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'insufficient target saving balance'
                }), 400

            wallet = WalletModel.query.filter_by(user_id=user_id, currency_ticker='ngn').first()

            decrypt_wallet_balance = Cryptographer.decrypt(wallet.fund)
            final_balance = float(decrypt_wallet_balance) + float(target_amount)
            MinimumBalance(final_balance)

            wallet.fund = Cryptographer.encrypt(final_balance)
            wallet.save()

            final_ts_balance = float(decrypt_balance) - float(target_amount)
            MinimumBalance(final_ts_balance)

            target_savings.balance = Cryptographer.encrypt(final_ts_balance)
            target_savings.save()

            if float(decrypt_balance) < 1:
                TargetSaveResource.delete_target_saving(id=id, user_id=user_id)

            currency_id = CurrencyModel.query.filter_by(short_code='ngn').first().id

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=Cryptographer.encrypt(target_amount),
                transaction_type='target_save_withdrawal',
                user_id=user_id,
                currency_id=currency_id,
                note=f"₦{float(target_amount):,} has been withdrawn from your target saving {target_savings.title}",
                status='successful',
                name=f'{target_savings.users.first_name} {target_savings.users.last_name}',
                transaction_flow='debit',
                transaction_title='Money Withdrawn',
                currency_ticker='ngn',
            )

            new_transaction.save()

            NotificationResource.store_nofication(
                title="Target Saving Withdrawal",
                body=f"₦{float(target_amount):,.2f} has been withdrawn from your target saving {target_savings.title}",
                user_id=user_id,
            )

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

    @staticmethod
    def delete_target_saving(id=None, user_id=None):
        """ """

        try:

            target_savings = TargetSaveModel.query.filter_by(user_id=user_id, id=id).first()

            if not target_savings:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'target savings not found'
                }), 404

            if target_savings.is_deleted:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'target saving already deleted'
                }), 400

            target_savings.is_deleted = True
            target_savings.deleted_at = datetime.now()
            target_savings.save()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'target savings has been successfully deleted'
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

    # @ TODO: background worker for automated saving from wallet to spend and save
