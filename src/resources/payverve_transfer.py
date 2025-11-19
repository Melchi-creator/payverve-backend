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

from .notification import NotificationResource
from ..models import CurrencyModel, \
    PayverveTransferModel, \
    SpendSaveModel, \
    TransactionModel, \
    UserModel, WalletModel
from ..utilities import Cryptographer, RandomGenerator, parse_params
from ..value_object import MinimumBalance


class PayverveTransferResource(Resource):
    """  """

    @staticmethod
    @parse_params(
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=True),
        Argument("account_number", location="json", required=True),
        Argument("user_id", location="json", required=True),
        Argument("wallet_id", location="json", required=True),
    )
    def create(amount, narration, account_number, user_id, wallet_id):
        """ """

        try:

            user_check = UserModel.query.filter_by(id=user_id).first()

            if not user_check:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'the user was not found'
                }), 404

            if len(account_number) != 10 or not account_number.isdigit():
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'receipient wallet id is not correct'
                }), 400

            MinimumBalance(int(amount))

            sender = WalletModel.query.filter_by(id=wallet_id).first()

            if not sender:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'the sender wallet was not found'
                }), 404

            if not sender.is_active:
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you do not have the facility to send money at the moment'
                }), 403

            decrypted_funds = Cryptographer.decrypt(sender.fund)

            if float(decrypted_funds) < float(amount):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'insufficient funds'
                }), 400

            recipient = WalletModel.query.filter_by(account_number=account_number).first()

            if not recipient:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'the recipient wallet id was not found'
                }), 404

            if not recipient.is_active:
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'the recipient does not have the facility to receive money at the moment'
                }), 403

            sender_currency = sender.currencies.short_code
            recipient_currency = recipient.currencies.short_code

            if not compare_digest(str(sender_currency), str(recipient_currency)):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you can only transfer money to a wallet with the same currency you are sending from'
                }), 400

            if compare_digest(str(sender.user_id), str(recipient.user_id)):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you cannot transfer money to yourself'
                }), 400

            transfer_amount = float(amount)

            decrypted_sender_funds = float(Cryptographer.decrypt(sender.fund))
            decrypted_recipient_funds = float(Cryptographer.decrypt(recipient.fund))

            sender_total_funds = float(decrypted_sender_funds) - float(amount)
            recipient_total_funds = float(decrypted_recipient_funds) + float(transfer_amount)

            sender.fund = Cryptographer.encrypt(sender_total_funds)
            recipient.fund = Cryptographer.encrypt(recipient_total_funds)

            reference_number = RandomGenerator.payverve_transfer_reference_number()

            # @TODO to be checked/updated to start real fx

            # whithdraw from sender Virtual Account
            # credit to receiver  Virtual Account
            # verify transaction status

            amount = Cryptographer.encrypt(amount)

            # noinspection PyArgumentList
            new_payverve_transfer = PayverveTransferModel(
                amount=amount,
                sender_name=f'{sender.users.first_name} {sender.users.last_name}',
                narration=narration,
                recipient_name=f'{recipient.users.first_name} {recipient.users.last_name}',
                recipient_account_number=account_number,
                reference=reference_number,
                user_id=user_id,
                wallet_id=wallet_id,
                transaction_status='successful'  # @TODO to be updated when real fx starts
            )

            new_payverve_transfer.save()

            sender.save()
            recipient.save()

            # sender transaction record

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=amount,
                transaction_type='payverve_transfer',
                user_id=user_id,
                currency_id=sender.currency_id,
                note=narration,
                status='successful',
                name=f'{recipient.users.first_name} {recipient.users.last_name}',
                transaction_flow='debit',
                transaction_title='Money Sent',
                currency_ticker=sender.currency_ticker.lower()
            )

            new_transaction.save()

            # recipient transaction record

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=amount,
                transaction_type='payverve_transfer',
                user_id=recipient.users.id,
                currency_id=sender.currency_id,
                note=narration,
                status='successful',
                name=f'{sender.users.first_name} {sender.users.last_name}',
                transaction_flow='credit',
                transaction_title='Money Received',
                currency_ticker=sender.currency_ticker.lower()
            )

            new_transaction.save()

            note_amount = Cryptographer.decrypt(amount)

            NotificationResource.store_nofication(
                title="Payverve Transfer",
                body=f"{sender.currency_ticker}{float(note_amount): ,.2f} was sent to {recipient.users.first_name} {recipient.users.last_name}",
                user_id=user_id,
            )

            # Spend and Save Transactions

            spend_save = SpendSaveModel.query.filter_by(user_id=user_id).first()

            if spend_save:
                if spend_save.is_active:
                    sender = WalletModel.query.filter_by(id=wallet_id).first()

                    amount = Cryptographer.decrypt(amount)

                    percentage_cal = (float(spend_save.percentage_to_save) / float(100))
                    amount_to_save = float(amount) * float(percentage_cal)

                    if float(Cryptographer.decrypt(sender.fund)) > float(amount_to_save):
                        init_balance = Cryptographer.decrypt(spend_save.balance)
                        final_balance = float(init_balance) + float(amount_to_save)

                        spend_save.balance = Cryptographer.encrypt(final_balance)
                        spend_save.save()

                        currency_id = CurrencyModel.query.filter_by(short_code=sender_currency).first().id

                        # noinspection PyArgumentList
                        new_transaction = TransactionModel(
                            amount=Cryptographer.encrypt(amount_to_save),
                            transaction_type='spend_and_save',
                            user_id=user_id,
                            currency_id=currency_id,
                            note=f"{spend_save.percentage_to_save}% of this transaction was saved under Spend & Save plan",
                            status='successful',
                            name=f"{user_check.first_name} {user_check.last_name}",
                            transaction_flow='debit',
                            transaction_title='Money Saved',
                            currency_ticker=sender_currency
                        )

                        new_transaction.save()

                        NotificationResource.store_nofication(
                            title="Spend Save",
                            body=f"₦{float(final_balance): ,.2f} was saved under Spend & Save plan",
                            user_id=user_id,
                        )

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'money transfered successfully'  # @ TODO change according to real fx
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

        payverve_transfers = PayverveTransferModel.query.order_by(PayverveTransferModel.created_at.desc()).all()

        try:
            if not payverve_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no payverve transfer was found'
                }), 404

            data = []

            for payverve_transfer in payverve_transfers:
                data.append({
                    'id': payverve_transfer.id,
                    'amount': Cryptographer.decrypt(payverve_transfer.amount),
                    'sender_name': payverve_transfer.sender_name,
                    'sender_bank': payverve_transfer.sender_bank,
                    'narration': payverve_transfer.narration,
                    'recipient_name': payverve_transfer.reference,
                    'recipient_bank': payverve_transfer.recipient_bank,
                    'recipient_account_number': payverve_transfer.recipient_account_number,
                    'reference': payverve_transfer.reference,
                    'transaction_type': payverve_transfer.transaction_type,
                    'transfer_pair': payverve_transfer.transfer_pair,
                    'transaction_status': payverve_transfer.transaction_status,
                    'user_id': payverve_transfer.user_id,
                    'wallet_id': payverve_transfer.wallet_id,
                    'created_at': payverve_transfer.created_at,
                    'updated_at': payverve_transfer.updated_at
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

        payverve_transfer = PayverveTransferModel.query.filter_by(id=id).first()

        try:
            if not payverve_transfer:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no payverve transfer was found'
                }), 404

            data = {
                'id': payverve_transfer.id,
                'amount': Cryptographer.decrypt(payverve_transfer.amount),
                'sender_name': payverve_transfer.sender_name,
                'sender_bank': payverve_transfer.sender_bank,
                'narration': payverve_transfer.narration,
                'recipient_name': payverve_transfer.reference,
                'recipient_bank': payverve_transfer.recipient_bank,
                'recipient_account_number': payverve_transfer.recipient_account_number,
                'reference': payverve_transfer.reference,
                'transaction_type': payverve_transfer.transaction_type,
                'transfer_pair': payverve_transfer.transfer_pair,
                'transaction_status': payverve_transfer.transaction_status,
                'user_id': payverve_transfer.user_id,
                'wallet_id': payverve_transfer.wallet_id,
                'created_at': payverve_transfer.created_at,
                'updated_at': payverve_transfer.updated_at
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
    def user_ptf_all(id=None):
        """ Retrieve all payverve transfer """

        payverve_transfers = PayverveTransferModel.query.filter_by(user_id=id).order_by(PayverveTransferModel.created_at.desc()).all()

        try:
            if not payverve_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no payverve transfer was found'
                }), 404

            data = []

            for payverve_transfer in payverve_transfers:
                data.append({
                    'id': payverve_transfer.id,
                    'amount': Cryptographer.decrypt(payverve_transfer.amount),
                    'sender_name': payverve_transfer.sender_name,
                    'sender_bank': payverve_transfer.sender_bank,
                    'narration': payverve_transfer.narration,
                    'recipient_name': payverve_transfer.reference,
                    'recipient_bank': payverve_transfer.recipient_bank,
                    'recipient_account_number': payverve_transfer.recipient_account_number,
                    'reference': payverve_transfer.reference,
                    'transaction_type': payverve_transfer.transaction_type,
                    'transfer_pair': payverve_transfer.transfer_pair,
                    'transaction_status': payverve_transfer.transaction_status,
                    'user_id': payverve_transfer.user_id,
                    'wallet_id': payverve_transfer.wallet_id,
                    'created_at': payverve_transfer.created_at,
                    'updated_at': payverve_transfer.updated_at
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

    # @TODO: remove the delete method or restrict its access in production
