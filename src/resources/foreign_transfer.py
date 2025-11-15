"""

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
    ProgrammingError, \
    SQLAlchemyError

import config
from ..middlewares import FlutterwaveHelper
from ..models import CurrencyModel, \
    ForeignTransferModel, \
    PayverveWalletModel, \
    SpendSaveModel, \
    TransactionModel, \
    UserModel, \
    WalletModel
from ..utilities import Cryptographer, RandomGenerator, parse_params


class ForeignTransferResource(Resource):
    """ T"""

    @staticmethod
    @parse_params(
        Argument("account", location="json", type=int, required=True),
        Argument("bank_code", location="json", type=int, required=True),
        Argument("bank_name", location="json", required=True),
    )
    def resolve_account(account, bank_code, bank_name):
        """ Resolve bank account details """

        try:

            if not bank_name:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'bank name is required'
                }), 400

            if not account:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'account number is required'
                }), 400

            if not bank_code:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'bank code is required'
                }), 400

            access_token = FlutterwaveHelper.flutterwave_authentication()
            response = FlutterwaveHelper.resolve_bank(account, bank_code, access_token)

            if not compare_digest(str(response.status_code), '200'):
                return jsonify({
                    'code': response.status_code,
                    'status_message': 'failed to resolve bank account',
                    'message': response.json().get('message', 'an error occurred while resolving bank account')
                }), response.status_code

            bank_data = response.json().get('data', {})

            bank_data['bank_name'] = bank_name

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': bank_data
            }), 200

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
    @parse_params(
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=True),
        Argument("account_number", location="json", required=True),
        Argument("recipient_name", location="json", required=True),
        Argument("recipient_bank", location="json", required=True),
        Argument("user_id", location="json", required=True),
        Argument("wallet_id", location="json", required=True),
    )
    def create(amount, narration, account_number, recipient_name, recipient_bank, user_id, wallet_id):
        """ """

        try:

            user_check = UserModel.query.filter_by(id=user_id).first()

            if not user_check:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'user not found'
                }), 404

            wallet_check = WalletModel.query.filter_by(id=wallet_id).first()

            if not wallet_check:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'wallet not found'
                }), 404

            if not compare_digest(str(wallet_check.user_id), str(user_id)):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you do not have access to this wallet'
                }), 403

            if compare_digest(str(wallet_check.currency_ticker).lower(), 'ngn'):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'foreign transfers cannot be made from NGN wallets'
                }), 400

            # @TODO: refactor the below to ensure the wallet currency is same as receipient bank currency

            # if not compare_digest(str(wallet_check.currency_ticker).lower(), 'ngn'):
            #     return jsonify({
            #         'code': 400,
            #         'status_message': 'bad request',
            #         'message': 'foreign transfers can only be made from NGN wallets'
            #     }), 400

            decrypt_fund = Cryptographer.decrypt(wallet_check.fund)

            if float(decrypt_fund) < float(amount):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'insufficient funds'
                }), 400

            # @TODO: integrate with payverve foreign bank transfer api here

            # whithdraw from sender Virtual Account and credit to receiver bank account
            # verify transaction status

            wallet_balance = float(decrypt_fund) - float(amount)
            wallet_check.fund = Cryptographer.encrypt(wallet_balance)
            wallet_check.save()

            reference_number = RandomGenerator.foreign_transfer_reference_number()
            amount = Cryptographer.encrypt(amount)

            # @TODO: get swift code from bank details api

            swift_code = int(RandomGenerator.swift_code())

            # noinspection PyArgumentList
            new_foreign_transfer = ForeignTransferModel(
                amount=amount,
                sender_name=f"{user_check.first_name} {user_check.last_name}",
                narration=narration,
                recipient_name=recipient_name,
                recipient_bank=recipient_bank,
                recipient_account_number=account_number,
                reference_number=reference_number,
                swift_code=swift_code,
                user_id=user_id,
                wallet_id=wallet_id,
                transfer_pair=f"{wallet_check.currency_ticker}-{wallet_check.currency_ticker}",
                transaction_status='successful'  # @TODO: change according to api response
            )
            new_foreign_transfer.save()

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=amount,
                transaction_type='international_transfer',
                user_id=user_id,
                currency_id=wallet_check.currency_id,
                note=narration,
                status='successful',
                name=recipient_name,
                transaction_flow='debit',
                transaction_title='Money Sent',
                currency_ticker=wallet_check.currency_ticker
            )

            new_transaction.save()

            # Spend and Save Transactions
            # @TODO: spend and save for foreign transfer should consider currency to ngn before saving
            spend_save = SpendSaveModel.query.filter_by(user_id=user_id).first()

            if spend_save:
                if spend_save.is_active:
                    sender = WalletModel.query.filter_by(user_id=user_id, currency_ticker='ngn').first()
                    currency_ticker = sender.currency_ticker.lower()

                    amount = Cryptographer.decrypt(amount)

                    # convert amount to NGN

                    token = None

                    # Extract token from Authorization header
                    if 'Authorization' in request.headers:
                        auth_header = request.headers['Authorization']
                        if auth_header.startswith('Bearer '):
                            try:
                                token = auth_header.split(' ')[1]

                            except IndexError:
                                return jsonify({
                                    "code": 401,
                                    'status_message': "Authentication token is missing",
                                    'message': "Token not found in Authorization header"
                                }), 401

                    payload = {
                        'base_currency': wallet_check.currency_ticker.lower(),
                        'target_currency': 'ngn',
                        'access_token': token
                    }

                    headers = {
                        "Authorization": f"Bearer {token}"
                    }

                    response = requests.request("POST",
                                                f"{config.app_path}/exchange-rates",
                                                headers=headers,
                                                json=payload)

                    if response.status_code != 200:
                        return jsonify({
                            'code': response.status_code,
                            'status_message': response.json().get('code_status', 'error'),
                            'message': response.json().get('data', 'could not fetch exchange rate')
                        }), response.status_code

                    exchange_rate = response.json().get("data").get("rate")

                    if int(exchange_rate) < 1:
                        payverve_charge = config.low_fx_payvevrve_charge  # charge for low exchange rates
                    else:
                        payverve_charge = config.high_fx_payverve_charge  # charge for high exchange rates

                    swap_amount = ((float(amount)) - (float(amount) * float(payverve_charge))) * float(exchange_rate)

                    payverve_balance = PayverveWalletModel.query.first()
                    payverve_charge_amount = (float(amount) * float(payverve_charge)) + float(Cryptographer.decrypt(payverve_balance.fund))

                    payverve_balance.fund = Cryptographer.encrypt(payverve_charge_amount)
                    payverve_balance.save()

                    # End of currency conversion

                    percentage_cal = (float(spend_save.percentage_to_save) / float(100))
                    amount_to_save = float(swap_amount) * float(percentage_cal)

                    if float(Cryptographer.decrypt(sender.fund)) > float(amount_to_save):
                        init_balance = Cryptographer.decrypt(spend_save.balance)
                        final_balance = float(init_balance) + float(amount_to_save)

                        spend_save.balance = Cryptographer.encrypt(final_balance)
                        spend_save.save()

                        currency_id = CurrencyModel.query.filter_by(short_code=currency_ticker).first().id

                        amount_to_save = Cryptographer.encrypt(amount_to_save)

                        # noinspection PyArgumentList
                        new_transaction = TransactionModel(
                            amount=amount_to_save,
                            transaction_type='spend_and_save',
                            user_id=user_id,
                            currency_id=currency_id,
                            note=f"{spend_save.percentage_to_save}% of this transaction was saved under Spend & Save plan",
                            status='successful',
                            name=f"{user_check.first_name} {user_check.last_name}",
                            transaction_flow='debit',
                            transaction_title='Money Saved',
                            currency_ticker=currency_ticker
                        )

                        new_transaction.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'transfer was done successfully',  # @ TODO change according to api response
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
        """ Retrieve all foreign transfers """

        foreign_transfers = ForeignTransferModel.query.order_by(ForeignTransferModel.created_at.desc()).all()

        try:
            if not foreign_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no foreign transfer history was found'
                }), 404

            data = []

            for foreign_transfer in foreign_transfers:
                data.append({
                    'id': foreign_transfer.id,
                    'amount': Cryptographer.decrypt(foreign_transfer.amount),
                    'sender_name': foreign_transfer.sender_name,
                    'sender_bank': foreign_transfer.sender_bank,
                    'narration': foreign_transfer.narration,
                    'recipient_name': foreign_transfer.recipient_name,
                    'recipient_bank': foreign_transfer.recipient_bank,
                    'recipient_account_number': foreign_transfer.recipient_account_number,
                    'transfer_type': foreign_transfer.transfer_type,
                    'transfer_pair': foreign_transfer.transfer_pair,
                    'transaction_status': foreign_transfer.transaction_status,
                    'user_id': foreign_transfer.user_id,
                    'wallet_id': foreign_transfer.wallet_id,
                    'created_at': foreign_transfer.created_at,
                    'updated_at': foreign_transfer.updated_at
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
        """  """

        foreign_transfer = ForeignTransferModel.query.filter_by(id=id).first()

        try:
            if not foreign_transfer:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no foreign transfer was found'
                }), 404

            data = {
                'id': foreign_transfer.id,
                'amount': Cryptographer.decrypt(foreign_transfer.amount),
                'sender_name': foreign_transfer.sender_name,
                'sender_bank': foreign_transfer.sender_bank,
                'narration': foreign_transfer.narration,
                'recipient_name': foreign_transfer.recipient_name,
                'recipient_bank': foreign_transfer.recipient_bank,
                'recipient_account_number': foreign_transfer.recipient_account_number,
                'transfer_type': foreign_transfer.transfer_type,
                'transfer_pair': foreign_transfer.transfer_pair,
                'transaction_status': foreign_transfer.transaction_status,
                'user_id': foreign_transfer.user_id,
                'wallet_id': foreign_transfer.wallet_id,
                'created_at': foreign_transfer.created_at,
                'updated_at': foreign_transfer.updated_at
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
    def user_ftf_all(id):
        """ Retrieve all foreign transfers """

        foreign_transfers = ForeignTransferModel.query.filter_by(user_id=id).order_by(ForeignTransferModel.created_at.desc()).all()

        try:
            if not foreign_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no foreign transfer history was found'
                }), 404

            data = []

            for foreign_transfer in foreign_transfers:
                data.append({
                    'id': foreign_transfer.id,
                    'amount': Cryptographer.decrypt(foreign_transfer.amount),
                    'sender_name': foreign_transfer.sender_name,
                    'sender_bank': foreign_transfer.sender_bank,
                    'narration': foreign_transfer.narration,
                    'recipient_name': foreign_transfer.recipient_name,
                    'recipient_bank': foreign_transfer.recipient_bank,
                    'recipient_account_number': foreign_transfer.recipient_account_number,
                    'transfer_type': foreign_transfer.transfer_type,
                    'transfer_pair': foreign_transfer.transfer_pair,
                    'transaction_status': foreign_transfer.transaction_status,
                    'user_id': foreign_transfer.user_id,
                    'wallet_id': foreign_transfer.wallet_id,
                    'created_at': foreign_transfer.created_at,
                    'updated_at': foreign_transfer.updated_at
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
