"""
swap_currency.py

Defines all functions for swapping currency especially CRUD
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
from ..models import PayverveWalletModel, SwapCurrencyModel, WalletModel
from ..utilities import Cryptographer, RandomGenerator, parse_params
from ..value_object import MinimumBalance


class SwapCurrencyResource(Resource):
    """ This class is concern with Swapping Currency Resources """

    @staticmethod
    @parse_params(
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=True),
        Argument("wallet_identifier", location="json", required=True),
        Argument("user_id", location="json", required=True),
        Argument("wallet_id", location="json", required=True),
    )
    def create(amount, narration, wallet_identifier, user_id, wallet_id):
        """ Swap Currency """

        # @ TODO: add a real fx charge system

        try:
            if len(wallet_identifier) != 10 or not wallet_identifier.isdigit():
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'message': 'the wallet id is not correct'
                }), 400

            MinimumBalance(int(amount))

            base_currency_wallet = WalletModel.query.filter_by(id=wallet_id, user_id=user_id).first()

            if not base_currency_wallet.is_active:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': f'your {base_currency_wallet.currencies.short_code} wallet does not have the facility to perform this operation'
                }), 403

            if not base_currency_wallet:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'message': 'the base currency wallet was not found'
                }), 404

            decrypted_funds = Cryptographer.decrypt(base_currency_wallet.fund)

            if float(decrypted_funds) < float(amount):
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'message': 'insufficient funds in base currency wallet'
                }), 400

            target_currency_wallet = WalletModel.query.filter_by(wallet_identifier=wallet_identifier,
                                                                 user_id=user_id).first()

            if not target_currency_wallet.is_active:
                return jsonify({
                    'code': 403,
                    'code_message': 'forbidden',
                    'message': f'your {target_currency_wallet.currencies.short_code} wallet does not have the facility to perform this operation'
                }), 403

            if not target_currency_wallet:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'message': 'the target currency wallet id was not found'
                }), 404

            base_currency = base_currency_wallet.currencies.short_code
            target_currency = target_currency_wallet.currencies.short_code

            exchange_rate = 1
            swap_amount = None

            if compare_digest(str(base_currency), str(target_currency)):
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'message': f'you can\'t convert from {base_currency} to {target_currency}'
                }), 400

            if not compare_digest(str(base_currency), str(target_currency)):
                access_token = request.cookies.get('access_token')

                payload = {
                    'base_currency': base_currency,
                    'target_currency': target_currency,
                    'access_token': access_token
                }

                headers = {
                    "Authorization": f"Bearer {access_token}"
                }

                response = requests.request("POST", f"{config.app_path}/exchange-rates", headers=headers, json=payload)

                if response.status_code != 200:
                    return jsonify({
                        'code': response.status_code,
                        'code_status': response.json().get('code_status', 'error'),
                        'data': response.json().get('data', 'could not fetch exchange rate')
                    }), response.status_code

                exchange_rate = response.json().get("data")

                if exchange_rate < 1:
                    payverve_charge = config.low_fx_payvevrve_charge  # charge for low exchange rates
                else:
                    payverve_charge = config.high_fx_payverve_charge  # charge for high exchange rates

                swap_amount = ((float(amount)) - (float(amount) * float(payverve_charge))) * float(exchange_rate)

                payverve_balance = PayverveWalletModel.query.first()
                payverve_charge_amount = (float(amount) * float(payverve_charge)) + float(Cryptographer.decrypt(
                    payverve_balance.fund))

                payverve_balance.fund = Cryptographer.encrypt(payverve_charge_amount)
                payverve_balance.save()

            decrypted_base_currency_wallet_funds = float(Cryptographer.decrypt(base_currency_wallet.fund))
            decrypted_target_currency_wallet_funds = float(Cryptographer.decrypt(target_currency_wallet.fund))

            base_currency_wallet_total_funds = float(decrypted_base_currency_wallet_funds) - float(amount)
            target_currency_wallet_total_funds = float(decrypted_target_currency_wallet_funds) + float(swap_amount)

            base_currency_wallet.fund = Cryptographer.encrypt(base_currency_wallet_total_funds)
            target_currency_wallet.fund = Cryptographer.encrypt(target_currency_wallet_total_funds)

            reference_number = RandomGenerator.swap_reference_number()

            # noinspection PyArgumentList
            new_currencies_swap = SwapCurrencyModel(
                amount_from_base_currency=Cryptographer.encrypt(amount),
                amount_to_target_currency=Cryptographer.encrypt(swap_amount),
                coversion_rate=exchange_rate,
                narration=narration,
                wallet_identifier=wallet_identifier,
                reference=reference_number,
                swap_pairs=f'Wallet({base_currency})-Wallet({target_currency})',
                user_id=user_id,
                wallet_id=wallet_id,
            )

            new_currencies_swap.save()

            base_currency_wallet.save()
            target_currency_wallet.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'currencies swapped successfully'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'message': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - data error',
                'message': 'ensure input data are correct'
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

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'code_status': 'calculation error - arithmetic, value, zerodivision error',
                'data': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all swapped currencies """

        swapped_currencies = SwapCurrencyModel.query.order_by(SwapCurrencyModel.created_at.desc()).all()

        try:
            if not swapped_currencies:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no swapped currency was found'
                }), 404

            data = []

            for swapped_currency in swapped_currencies:
                data.append({
                    'id': swapped_currency.id,
                    'amount_from_base_currency': Cryptographer.decrypt(swapped_currency.amount_from_base_currency),
                    'amount_to_target_currency': Cryptographer.decrypt(swapped_currency.amount_to_target_currency),
                    'coversion_rate': swapped_currency.coversion_rate,
                    'narration': swapped_currency.narration,
                    'wallet_identifier': swapped_currency.wallet_identifier,
                    'reference': swapped_currency.reference,
                    'transaction_type': swapped_currency.transaction_type,
                    'swap_pairs': swapped_currency.swap_pairs,
                    'user_id': swapped_currency.user_id,
                    'user': swapped_currency.users.first_name + ' ' + swapped_currency.users.last_name,
                    'wallet_id': swapped_currency.wallet_id,
                    'created_at': swapped_currency.created_at,
                    'updated_at': swapped_currency.updated_at
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
        """ Retrieve one swapped currency by id """

        swapped_currency = SwapCurrencyModel.query.filter_by(id=id).first()

        try:
            if not swapped_currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no swapped currency was found'
                }), 404

            data = {
                'id': swapped_currency.id,
                'amount_from_base_currency': Cryptographer.decrypt(swapped_currency.amount_from_base_currency),
                'amount_to_target_currency': Cryptographer.decrypt(swapped_currency.amount_to_target_currency),
                'coversion_rate': swapped_currency.coversion_rate,
                'narration': swapped_currency.narration,
                'wallet_identifier': swapped_currency.wallet_identifier,
                'reference': swapped_currency.reference,
                'transaction_type': swapped_currency.transaction_type,
                'swap_pairs': swapped_currency.swap_pairs,
                'user_id': swapped_currency.user_id,
                'user': swapped_currency.users.first_name + ' ' + swapped_currency.users.last_name,
                'wallet_id': swapped_currency.wallet_id,
                'created_at': swapped_currency.created_at,
                'updated_at': swapped_currency.updated_at
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
        """ Retrieve and delete one swapped currency by id """

        swapped_currency = SwapCurrencyModel.query.filter_by(id=id).first()

        try:
            if not swapped_currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no swapped currency was found'
                }), 404

            swapped_currency.delete()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'swap history was deleted successfully'
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
