"""
src/resources/payverve_transfer.py
This module defines the PayverveTransferResource class, which handles Payverve transfer operations.
It includes methods for creating, reading, and deleting Payverve transfers, with error handling for
various database and validation errors.
"""
import secrets
from hmac import compare_digest

from flask import jsonify, request
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
    VirtualAccountNumberModel,  db, \
    PayverveTransferModel, \
    SpendSaveModel, \
    TransactionModel, \
    UserModel, WalletModel
from ..utilities import Cryptographer, KYCTierCheck, RandomGenerator, parse_params
from ..value_object import MinimumBalance


class PayverveTransferResource(Resource):
    """ Handles PayVerve-to-PayVerve (internal) transfers """

    @staticmethod
    @parse_params(
        Argument("account_number", location="json", required=True),
        Argument("wallet_id", location="json", required=True),
    )
    def resolve_account(account_number, wallet_id):
        """ Resolves a PayVerve internal account number to the recipient's name,
        without executing a transfer. Used to preview a transfer before payment. """
        try:
            sender_id = request.current_user['sub']

            sender_wallet = WalletModel.query.filter_by(id=wallet_id).first()

            if not sender_wallet:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'sender wallet not found'
                }), 404

            if not compare_digest(str(sender_wallet.user_id), str(sender_id)):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you do not have access to this wallet'
                }), 403

            virtual_account = VirtualAccountNumberModel.query.filter_by(
                account_number=account_number, is_active=True
            ).first()

            if not virtual_account:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no PayVerve account found with this account number'
                }), 404

            if compare_digest(str(virtual_account.user_id), str(sender_id)):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you cannot send money to yourself'
                }), 400

            receiver = UserModel.query.filter_by(
                id=virtual_account.user_id).first()

            if not receiver or receiver.deleted or not receiver.account_active:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'this account is not available to receive transfers'
                }), 404

            if not compare_digest(
                str(sender_wallet.currency_ticker).lower(),
                str(virtual_account.currency_ticker).lower()
            ):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'sender and receiver currencies do not match'
                }), 400

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': {
                    'account_number': virtual_account.account_number,
                    'account_name': f"{receiver.first_name} {receiver.last_name}",
                    'currency_ticker': virtual_account.currency_ticker,
                }
            }), 200

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all payverve transfers """

        payverve_transfers = PayverveTransferModel.query.order_by(
            PayverveTransferModel.created_at.desc()).all()

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
                    'charge_amount': payverve_transfer.charge_amount,
                    'sender_name': payverve_transfer.sender_name,
                    'sender_bank': payverve_transfer.sender_bank,
                    'sender_account_number': payverve_transfer.sender_account_number,
                    'narration': payverve_transfer.narration,
                    'recipient_name': payverve_transfer.recipient_name,
                    'recipient_bank': payverve_transfer.recipient_bank,
                    'recipient_account_number': payverve_transfer.recipient_account_number,
                    'reference': payverve_transfer.reference,
                    'transaction_type': payverve_transfer.transaction_type,
                    'transfer_pair': payverve_transfer.transfer_pair,
                    'transaction_status': payverve_transfer.transaction_status,
                    'user_id': payverve_transfer.user_id,
                    'wallet_id': payverve_transfer.wallet_id,
                    'created_at': payverve_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': payverve_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if payverve_transfer.updated_at else None,
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

        payverve_transfer = PayverveTransferModel.query.filter_by(
            id=id).first()

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
                'charge_amount': payverve_transfer.charge_amount,
                'sender_name': payverve_transfer.sender_name,
                'sender_bank': payverve_transfer.sender_bank,
                'sender_account_number': payverve_transfer.sender_account_number,
                'narration': payverve_transfer.narration,
                'recipient_name': payverve_transfer.recipient_name,
                'recipient_bank': payverve_transfer.recipient_bank,
                'recipient_account_number': payverve_transfer.recipient_account_number,
                'reference': payverve_transfer.reference,
                'transaction_type': payverve_transfer.transaction_type,
                'transfer_pair': payverve_transfer.transfer_pair,
                'transaction_status': payverve_transfer.transaction_status,
                'user_id': payverve_transfer.user_id,
                'wallet_id': payverve_transfer.wallet_id,
                'created_at': payverve_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': payverve_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if payverve_transfer.updated_at else None,
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
        """ Retrieve all payverve transfers for a specific user """

        payverve_transfers = PayverveTransferModel.query.filter_by(
            user_id=id).order_by(PayverveTransferModel.created_at.desc()).all()

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
                    'charge_amount': payverve_transfer.charge_amount,
                    'sender_name': payverve_transfer.sender_name,
                    'sender_bank': payverve_transfer.sender_bank,
                    'sender_account_number': payverve_transfer.sender_account_number,
                    'narration': payverve_transfer.narration,
                    'recipient_name': payverve_transfer.recipient_name,
                    'recipient_bank': payverve_transfer.recipient_bank,
                    'recipient_account_number': payverve_transfer.recipient_account_number,
                    'reference': payverve_transfer.reference,
                    'transaction_type': payverve_transfer.transaction_type,
                    'transfer_pair': payverve_transfer.transfer_pair,
                    'transaction_status': payverve_transfer.transaction_status,
                    'user_id': payverve_transfer.user_id,
                    'wallet_id': payverve_transfer.wallet_id,
                    'created_at': payverve_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': payverve_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if payverve_transfer.updated_at else None,
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
    @parse_params(
        Argument("wallet_id", location="json", required=True),
        Argument("account_number", location="json", required=True),
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=False),
        Argument("transaction_pin", location="json", required=True),
    )
    def create(wallet_id, account_number, amount, narration, transaction_pin):
        """ Executes a PayVerve-to-PayVerve wallet transfer """

        try:
            sender_id = request.current_user['sub']

            amount = float(amount)

            if amount <= 0:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'amount must be greater than zero'
                }), 400

            # KYC Tier Check — sender's transfer limits
            kyc_check = KYCTierCheck.kyc_transfer_check(
                sender_id, amount, 'payverve')
            if kyc_check is not None:
                return kyc_check

            sender = UserModel.query.filter_by(id=sender_id).first()

            if not sender:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'sender not found'
                }), 404

            if not sender.transaction_pin:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'please set up a transaction PIN before making transfers'
                }), 400

            if not sender.check_transaction_pin(transaction_pin):
                return jsonify({
                    'code': 401,
                    'status_message': 'unauthorized',
                    'message': 'incorrect transaction PIN'
                }), 401

            sender_wallet = WalletModel.query.filter_by(id=wallet_id).first()

            if not sender_wallet:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'sender wallet not found'
                }), 404

            if not compare_digest(str(sender_wallet.user_id), str(sender_id)):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you do not have access to this wallet'
                }), 403

            virtual_account = VirtualAccountNumberModel.query.filter_by(
                account_number=account_number, is_active=True
            ).first()

            if not virtual_account:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no PayVerve account found with this account number'
                }), 404

            if compare_digest(str(virtual_account.user_id), str(sender_id)):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'you cannot send money to yourself'
                }), 400

            receiver = UserModel.query.filter_by(
                id=virtual_account.user_id).first()

            if not receiver or receiver.deleted or not receiver.account_active:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'this account is not available to receive transfers'
                }), 404

            if not compare_digest(
                str(sender_wallet.currency_ticker).lower(),
                str(virtual_account.currency_ticker).lower()
            ):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'sender and receiver currencies do not match'
                }), 400

            receiver_wallet = WalletModel.query.filter_by(
                user_id=receiver.id,
                currency_id=sender_wallet.currency_id
            ).first()

            if not receiver_wallet:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'recipient does not have a matching currency wallet'
                }), 404

            sender_balance = float(Cryptographer.decrypt(sender_wallet.fund))

            if sender_balance < amount:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'insufficient funds'
                }), 400

            receiver_balance = float(
                Cryptographer.decrypt(receiver_wallet.fund))
            projected_receiver_balance = receiver_balance + amount

            # KYC Tier Check — receiver's resulting balance cap
            kyc_balance_check = KYCTierCheck.kyc_balance_check(
                receiver.id, projected_receiver_balance, 'payverve'
            )
            if kyc_balance_check is not None:
                return kyc_balance_check

            sender_virtual_account = VirtualAccountNumberModel.query.filter_by(
                user_id=sender_id, currency_id=sender_wallet.currency_id
            ).first()

            sender_account_number = sender_virtual_account.account_number if sender_virtual_account else 0

            reference = f"PVT-{secrets.token_hex(8).upper()}"
            session_id = secrets.token_urlsafe(16)

            # --- Debit sender, credit receiver, single atomic commit ---

            new_sender_balance = sender_balance - amount
            sender_wallet.fund = Cryptographer.encrypt(str(new_sender_balance))

            receiver_wallet.fund = Cryptographer.encrypt(
                str(projected_receiver_balance))

            sender_name = f"{sender.first_name} {sender.last_name}"
            receiver_name = f"{receiver.first_name} {receiver.last_name}"

            # noinspection PyArgumentList
            new_payverve_transfer = PayverveTransferModel(
                amount=Cryptographer.encrypt(str(amount)),
                charge_amount=0.0,
                sender_name=sender_name,
                sender_account_number=int(sender_account_number),
                narration=narration,
                recipient_name=receiver_name,
                recipient_account_number=int(virtual_account.account_number),
                reference=reference,
                session_id=session_id,
                stamp_duty=0.0,
                transfer_pair=f"{sender_wallet.currency_ticker.lower()}-{receiver_wallet.currency_ticker.lower()}",
                transaction_status='successful',
                user_id=sender_id,
                wallet_id=sender_wallet.id,
            )

            # noinspection PyArgumentList
            debit_transaction = TransactionModel(
                amount=Cryptographer.encrypt(str(amount)),
                transaction_type='payverve_transfer',
                user_id=sender_id,
                currency_id=sender_wallet.currency_id,
                note=narration,
                status='successful',
                name=receiver_name,
                transaction_flow='debit',
                transaction_title='Money Sent',
                currency_ticker=sender_wallet.currency_ticker.lower(),
            )

            # noinspection PyArgumentList
            credit_transaction = TransactionModel(
                amount=Cryptographer.encrypt(str(amount)),
                transaction_type='payverve_transfer',
                user_id=receiver.id,
                currency_id=receiver_wallet.currency_id,
                note=narration,
                status='successful',
                name=sender_name,
                transaction_flow='credit',
                transaction_title='Money Received',
                currency_ticker=receiver_wallet.currency_ticker.lower(),
            )

            db.session.add(sender_wallet)
            db.session.add(receiver_wallet)
            db.session.add(new_payverve_transfer)
            db.session.add(debit_transaction)
            db.session.add(credit_transaction)
            db.session.commit()

            NotificationResource.store_nofication(
                title="Money Sent",
                body=f"{sender_wallet.currency_ticker.upper()} {amount:,.2f} was sent to {receiver_name}",
                user_id=sender_id,
            )

            NotificationResource.store_nofication(
                title="Money Received",
                body=f"{receiver_wallet.currency_ticker.upper()} {amount:,.2f} was received from {sender_name}",
                user_id=receiver.id,
            )

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'transfer successful',
                'data': {
                    'reference': reference,
                    'amount': amount,
                    'recipient_name': receiver_name,
                }
            }), 201

        except IntegrityError:
            db.session.rollback()
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'a conflict occurred while processing this transfer'
            }), 409

        except DataError:
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except (OperationalError, DisconnectionError, InternalError, ProgrammingError, SQLAlchemyError):
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not complete transfer'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'invalid amount'
            }), 400

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    # @TODO: remove the delete method or restrict its access in production
