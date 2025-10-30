"""
src/resources/payverve_transfer.py
This module defines the PayverveTransferResource class, which handles Payverve transfer operations.
It includes methods for creating, reading, and deleting Payverve transfers, with error handling for
various database and validation errors.
"""
from hmac import compare_digest

import requests
from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, SQLAlchemyError

import config
from ..models import CurrencyModel, \
    PayverveTransferModel, \
    PayverveWalletModel, \
    SpendSaveModel, \
    TransactionModel, \
    WalletModel
from ..utilities import Cryptographer, RandomGenerator, parse_params
from ..value_object import MinimumBalance


class PayverveTransferResource(Resource):
    """  """

    @staticmethod
    @parse_params(
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=True),
        Argument("wallet_identifier", location="json", required=True),
        Argument("user_id", location="json", required=True),
        Argument("wallet_id", location="json", required=True),
    )
    def create(amount, narration, wallet_identifier, user_id, wallet_id):
        """ """

        try:
            if len(wallet_identifier) != 10 or not wallet_identifier.isdigit():
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'the wallet id is not correct'
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
                    'message': 'insufficient funds in sender wallet'
                }), 400

            recipient = WalletModel.query.filter_by(wallet_identifier=wallet_identifier).first()

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

            # @TODO to be update (removed) when accepting other currencies

            if not compare_digest(str(sender_currency), 'ngn') or not compare_digest(str(recipient_currency), 'ngn'):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'sender currency and recipient currency must be ngn'
                })

            exchange_rate = 1
            transfer_amount = None

            if compare_digest(str(sender_currency), str(recipient_currency)):
                transfer_amount = (float(amount) * float(exchange_rate))

            if not compare_digest(str(sender_currency), str(recipient_currency)):
                access_token = None

                # Extract token from Authorization header
                if 'Authorization' in request.headers:
                    auth_header = request.headers['Authorization']
                    if auth_header.startswith('Bearer '):
                        access_token = auth_header.split(' ')[1]

                payload = {
                    'base_currency': sender_currency,
                    'target_currency': recipient_currency,
                    'access_token': access_token
                }

                headers = {
                    "Authorization": f"Bearer {access_token}"
                }

                response = requests.request("POST", f"{config.app_path}/exchange-rates", headers=headers, json=payload)

                if response.status_code != 200:
                    return jsonify({
                        'code': response.status_code,
                        'status_message': response.json().get('code_status', 'error'),
                        'message': response.json().get('data', 'could not fetch exchange rate')
                    }), response.status_code

                exchange_rate = response.json().get("data")

                if exchange_rate < 1:
                    payverve_charge = config.low_fx_payvevrve_charge  # charge for low exchange rates
                else:
                    payverve_charge = config.high_fx_payverve_charge  # charge for high exchange rates

                transfer_amount = ((float(amount)) - (float(amount) * float(payverve_charge))) * float(exchange_rate)

                payverve_balance = PayverveWalletModel.query.first()
                payverve_charge_amount = (float(amount) * float(payverve_charge)) + float(Cryptographer.decrypt(
                    payverve_balance.fund))

                payverve_balance.fund = Cryptographer.encrypt(payverve_charge_amount)
                payverve_balance.save()

            decrypted_sender_funds = float(Cryptographer.decrypt(sender.fund))
            decrypted_recipient_funds = float(Cryptographer.decrypt(recipient.fund))

            sender_total_funds = float(decrypted_sender_funds) - float(amount)
            recipient_total_funds = float(decrypted_recipient_funds) + float(transfer_amount)

            sender.fund = Cryptographer.encrypt(sender_total_funds)
            recipient.fund = Cryptographer.encrypt(recipient_total_funds)

            reference_number = RandomGenerator.payverve_transfer_reference_number()

            # noinspection PyArgumentList
            new_payverve_transfer = PayverveTransferModel(
                amount_from_sender=Cryptographer.encrypt(amount),
                amount_to_recipient=Cryptographer.encrypt(transfer_amount),
                coversion_rate=exchange_rate,
                narration=narration,
                wallet_identifier=wallet_identifier,
                reference=reference_number,
                transfer_pair=f'Wallet({sender_currency})-Wallet({recipient_currency})',
                user_id=user_id,
                wallet_id=wallet_id,
            )

            new_payverve_transfer.save()

            sender.save()
            recipient.save()

            # Spend and Save Transactions

            spend_save = SpendSaveModel.query.filter_by(user_id=user_id).first()

            if spend_save:
                if spend_save.is_active:
                    sender = WalletModel.query.filter_by(id=wallet_id).first()

                    percentage_cal = (int(spend_save.percentage_to_save) / int(100))
                    amount_to_save = int(amount) * int(percentage_cal)

                    if sender.fund > amount_to_save:
                        init_balance = Cryptographer.decrypt(spend_save.balance)
                        final_balance = float(init_balance) + float(amount_to_save)

                        spend_save.balance = Cryptographer.encrypt(final_balance)
                        spend_save.save()

                        currency_id = CurrencyModel.query.filter_by(short_code=sender_currency).first().id

                        # noinspection PyArgumentList
                        new_transaction = TransactionModel(
                            amount=amount_to_save,
                            transaction_type='spend_and_save',
                            user_id=user_id,
                            currency_id=currency_id,
                            note=f'spend and save at {spend_save.percentage_to_save}%',
                        )

                        new_transaction.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'money transfered successfully'
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
                    'amount_from_sender': Cryptographer.decrypt(payverve_transfer.amount_from_sender),
                    'amount_to_recipient': Cryptographer.decrypt(payverve_transfer.amount_to_recipient),
                    'coversion_rate': payverve_transfer.coversion_rate,
                    'narration': payverve_transfer.narration,
                    'wallet_identifier': payverve_transfer.wallet_identifier,
                    'reference': payverve_transfer.reference,
                    'transaction_type': payverve_transfer.transaction_type,
                    'transfer_pair': payverve_transfer.transfer_pair,
                    'user_id': payverve_transfer.user_id,
                    'sender': payverve_transfer.users.first_name + ' ' + payverve_transfer.users.last_name,
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
                'amount_from_sender': Cryptographer.decrypt(payverve_transfer.amount_from_sender),
                'amount_to_recipient': Cryptographer.decrypt(payverve_transfer.amount_to_recipient),
                'coversion_rate': payverve_transfer.coversion_rate,
                'narration': payverve_transfer.narration,
                'wallet_identifier': payverve_transfer.wallet_identifier,
                'reference': payverve_transfer.reference,
                'transaction_type': payverve_transfer.transaction_type,
                'transfer_pair': payverve_transfer.transfer_pair,
                'user_id': payverve_transfer.user_id,
                'sender': payverve_transfer.users.first_name + ' ' + payverve_transfer.users.last_name,
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
    def delete(id=None):
        """ Retrieve and delete one payverve tranfer by id """

        payverve_transfer = PayverveTransferModel.query.filter_by(id=id).first()

        try:
            if not payverve_transfer:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no payverve transfer was found'
                }), 404

            payverve_transfer.delete()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'swap history was deleted successfully'
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
