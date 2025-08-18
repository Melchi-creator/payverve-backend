"""
src/resources/exchange_rate.py
This module defines the ExchangeRateResource class, which provides methods to create, read,
and manage exchange rates. It interacts with the ExchangeRateModel to handle currency pairs,
"""
from datetime import datetime

import requests
from flask import jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, \
    SQLAlchemyError

import config
from ..models import ExchangeRateModel


class ExchangeRateResource(Resource):
    """ Exchange Rate Resource """

    @staticmethod
    def create():
        """ Create a new exchange rate for a currency pair """

        try:

            base_currency = request.json.get('base_currency')
            target_currency = request.json.get('target_currency')
            access_token = request.json.get('access_token')

            check_today_pair = ExchangeRateModel.query.filter_by(base_currency=base_currency,
                                                                 target_currency=target_currency).order_by(
                ExchangeRateModel.created_at.desc()).first()

            today_rate = None
            confirm_is_today = None

            if check_today_pair:
                confirm_is_today = check_today_pair.created_at.date() == datetime.now().date()

                if confirm_is_today:
                    today_rate = check_today_pair.rate

            if confirm_is_today is None:
                payload = {
                    'base_currency': base_currency,
                    'target_currency': target_currency
                }

                headers = {
                    "Authorization": f"Bearer {access_token}"
                }

                response = requests.request("POST",
                                            f"{config.app_path}/exchange-rates-api",
                                            headers=headers,
                                            json=payload)

                if response.status_code != 200:
                    return jsonify({
                        'code': response.status_code,
                        'code_status': 'error',
                        'data': 'could not fetch exchange rate'
                    }), response.status_code

                today_rate = float(response.text)

                # noinspection PyArgumentList
                new_exchange_rate = ExchangeRateModel(
                    base_currency=base_currency,
                    target_currency=target_currency,
                    rate=today_rate,
                )
                new_exchange_rate.save()

            return jsonify({
                'code': 200,
                'code_status': 'successful',
                'data': today_rate
            }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'message': 'this currency pair has already been listed'
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
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
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
                    'message': 'no currency pair was found'
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
                    'message': 'no currency pair was found'
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
