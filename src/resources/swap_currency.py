"""
swap_currency.py

Defines all functions for swapping currency especially CRUD
"""
from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, \
    SQLAlchemyError

from .. import config
from ..models import CurrencyModel, ExchangeRateModel, SwapCurrencyModel, WalletModel
from ..utilities import RandomGenerator, parse_params


class SwapCurrencyResource(Resource):
    """ This class is concern with Swapping Currency Resources """

    @staticmethod
    @parse_params(
        Argument("base_currency", location="json", required=True),
        Argument("target_currency", location="json", required=True),
        Argument("amount", location="json", required=True),
        Argument("user", location="json", required=True),
    )
    def create(base_currency, target_currency, amount, user):
        """ Swap Currency """

        try:
            exchange_rate = ExchangeRateModel.query.filter_by(
                base_currency=base_currency,
                target_currency=target_currency).first()

            check_currency = CurrencyModel.query.filter_by(short_code=base_currency).first()

            check_balance = None

            if check_currency:
                check_balance = WalletModel.query.filter_by(user=user, currency=check_currency.id).first()

            if not exchange_rate:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'there is no exchange rate for this pair'
                }), 404

            if not check_balance or not check_currency:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'could not find the base wallet'
                }), 404

            if float(amount) > check_balance.fund:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'your balance is not up to the inputted amount'
                }), 400

            currency = CurrencyModel.query.filter_by(short_code=target_currency).first()

            wallet = None

            if currency:
                wallet = WalletModel.query.filter_by(user=user, currency=currency.id).first()

            if not wallet or not currency:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'could not find the target wallet'
                }), 404

            converted_amount = float(amount) * (
                    float(exchange_rate.rate) - (float(exchange_rate.rate) * float(config.exchange_rate_markup)))
            wallet.fund += float(converted_amount)
            check_balance.fund -= float(amount)

            # noinspection PyArgumentList
            new_swap_currency = SwapCurrencyModel(
                base_currency=base_currency,
                target_currency=target_currency,
                amount=amount,
                currency_pair=f'{base_currency.upper()}-{target_currency.upper()}',
                amount_received=converted_amount,
                reference=RandomGenerator.swap_reference_number(),
                user=user,
            )
            wallet.save()
            check_balance.save()
            new_swap_currency.save()

            data = {
                'id': new_swap_currency.id,
                'base_currency': new_swap_currency.base_currency,
                'target_currency': new_swap_currency.target_currency,
                'amount': new_swap_currency.amount,
                'transaction_type': new_swap_currency.transaction_type,
                'currency_pair': new_swap_currency.currency_pair,
                'amount_received': new_swap_currency.amount_received,
                'reference': new_swap_currency.reference,
                'user': new_swap_currency.user,
            }

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': {
                    'data': 'currency was swaped successfully',
                    'details': data
                }
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'data': 'this currency has already been listed'
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

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'code_status': 'calculation error - arithmetic, value, zerodivision error',
                'data': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all swapped currencies """

        swapped_currencies = SwapCurrencyModel.query.all()

        try:
            if not swapped_currencies:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no swapped currency was found'
                }), 404

            data = []

            for swapped_currency in swapped_currencies:
                data.append({
                    'id': swapped_currency.id,
                    'base_currency': swapped_currency.base_currency,
                    'target_currency': swapped_currency.target_currency,
                    'amount': swapped_currency.amount,
                    'transaction_type': swapped_currency.transaction_type,
                    'currency_pair': swapped_currency.currency_pair,
                    'amount_received': swapped_currency.amount_received,
                    'reference': swapped_currency.reference,
                    'user': swapped_currency.user,
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
                    'data': 'no swapped currency was found'
                }), 404

            data = {
                'id': swapped_currency.id,
                'base_currency': swapped_currency.base_currency,
                'target_currency': swapped_currency.target_currency,
                'amount': swapped_currency.amount,
                'transaction_type': swapped_currency.transaction_type,
                'currency_pair': swapped_currency.currency_pair,
                'amount_received': swapped_currency.amount_received,
                'reference': swapped_currency.reference,
                'user': swapped_currency.user,
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
                    'data': 'no swapped currency was found'
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
