"""
exchange_rate.py

Defines all functions for exchnage rate especially CRUD
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

from ..models import CurrencyModel, ExchangeRateModel
from ..utilities import parse_params


class ExchangeRateResource(Resource):
    """ This class is concern with Exchange Rate Resources """

    @staticmethod
    @parse_params(
        Argument("base_currency", location="json", required=True),
        Argument("target_currency", location="json", required=True),
        Argument("rate", location="json", required=True),
    )
    def create(base_currency, target_currency, rate):
        """ Adds a new exchange rate """

        exchange_rate = ExchangeRateModel.query.filter_by(
            base_currency=base_currency,
            target_currency=target_currency).all()

        try:
            if exchange_rate:
                return jsonify({
                    'code': 409,
                    'code_status': 'conflict',
                    'data': 'the currency pair already exist'
                }), 409

            check_base_currency = CurrencyModel.query.filter_by(short_code=base_currency).first()
            check_target_currency = CurrencyModel.query.filter_by(short_code=target_currency).first()

            if not check_base_currency or not check_target_currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'base or target currency was not found'
                }), 404

            # noinspection PyArgumentList
            new_exchange_rate = ExchangeRateModel(
                base_currency=base_currency,
                target_currency=target_currency,
                rate=rate,
            )
            new_exchange_rate.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'currency pair was successfully added'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'data': 'this currency pair has already been listed'
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

    @staticmethod
    def read_all():
        """ Retrieve all exchange rate """

        exchange_rates = ExchangeRateModel.query.all()

        try:
            if not exchange_rates:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no currency pair was found'
                }), 404

            data = []

            for exchange_rate in exchange_rates:
                data.append({
                    'id': exchange_rate.id,
                    'base_currency': exchange_rate.base_currency,
                    'target_currency': exchange_rate.target_currency,
                    'rate': exchange_rate.rate,
                    'created_at': exchange_rate.created_at,
                    'updated_at': exchange_rate.updated_at
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
        """ Retrieve a wallet by id """

        exchange_rate = ExchangeRateModel.query.filter_by(id=id).first()

        try:
            if not exchange_rate:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no currency pair was found'
                }), 404

            data = {
                'id': exchange_rate.id,
                'base_currency': exchange_rate.base_currency,
                'target_currency': exchange_rate.target_currency,
                'rate': exchange_rate.rate,
                'created_at': exchange_rate.created_at,
                'updated_at': exchange_rate.updated_at
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
    @parse_params(
        Argument("base_currency", location="json"),
        Argument("target_currency", location="json"),
        Argument("rate", location="json"),
    )
    def update(id=None, **fields):
        """ Updates a wallet by id """

        exchange_rate = ExchangeRateModel.query.filter_by(id=id).first()

        try:
            if not exchange_rate:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no currency pair was found'
                }), 404

            if 'base_currency' in fields and fields['base_currency'] is not None:
                exchange_rate.base_currency = fields['base_currency']

            if 'target_currency' in fields and fields['target_currency'] is not None:
                exchange_rate.target_currency = fields['target_currency']

            if 'rate' in fields and fields['rate'] is not None:
                exchange_rate.rate = fields['rate']

            exchange_rate.save()

            data = {
                'id': exchange_rate.id,
                'base_currency': exchange_rate.base_currency,
                'target_currency': exchange_rate.target_currency,
                'rate': exchange_rate.rate,
                'created_at': exchange_rate.created_at,
                'updated_at': exchange_rate.updated_at
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
        """ Retrieve and delete a wallet by id """

        exchange_rate = ExchangeRateModel.query.filter_by(id=id).first()

        try:
            if not exchange_rate:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no currency pair was found'
                }), 404

            exchange_rate.delete()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'wallet was deleted successfully'
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
