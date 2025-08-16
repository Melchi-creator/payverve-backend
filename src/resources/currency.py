"""
src/resources/currency.py
This module defines the CurrencyResource class, which provides RESTful endpoints for managing currencies.
It includes methods for creating, reading, updating, and deleting currencies, with appropriate error handling and
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

from ..models import CurrencyModel, PayverveWalletModel
from ..utilities import Cryptographer, parse_params


class CurrencyResource(Resource):
    """ Currency Resource """

    @staticmethod
    @parse_params(
        Argument("name", location="json", required=True),
        Argument("short_code", location="json", required=True),
        Argument("country", location="json", required=True),
    )
    def create(name, short_code, country):
        """ Create a new currency """

        currencies = CurrencyModel.query.all()

        try:
            for currency in currencies:
                if name.lower() in currency.name or short_code.lower() in currency.short_code or country.lower() in currency.country:
                    return jsonify({
                        'code': 409,
                        'code_status': 'conflict',
                        'message': 'this currency has already been listed'
                    }), 409

            # noinspection PyArgumentList
            new_currency = CurrencyModel(
                name=name.lower(),
                short_code=short_code.lower(),
                country=country.lower()
            )
            new_currency.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'currency was successfully added'
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
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all currencies """

        currencies = CurrencyModel.query.order_by(CurrencyModel.name.asc()).all()

        try:
            if not currencies:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no currency was found'
                }), 404

            data = []

            for currency in currencies:
                data.append({
                    'id': currency.id,
                    'name': currency.name,
                    'short_code': currency.short_code,
                    'country': currency.country,
                    'created_at': currency.created_at,
                    'updated_at': currency.updated_at
                })

            payverve_wallet = PayverveWalletModel.query.first()

            if not payverve_wallet:
                # noinspection PyArgumentList
                new_payverve_wallet = PayverveWalletModel(
                    fund=Cryptographer.encrypt('0.0')
                )
                new_payverve_wallet.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """ Retrieve a currency by id """

        currency = CurrencyModel.query.filter_by(id=id).first()

        try:
            if not currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no currency was found'
                }), 404

            data = {
                'id': currency.id,
                'name': currency.name,
                'short_code': currency.short_code,
                'country': currency.country,
                'created_at': currency.created_at,
                'updated_at': currency.updated_at
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
        Argument("name", location="json"),
        Argument("short_code", location="json"),
        Argument("country", location="json"),
    )
    def update(id=None, **fields):
        """ Updates a currency by id """

        currency = CurrencyModel.query.filter_by(id=id).first()

        try:
            if not currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no currency was found'
                }), 404

            if 'name' in fields and fields['name'] is not None:
                currency.name = fields['name'].lower()

            if 'short_code' in fields and fields['short_code'] is not None:
                currency.short_code = fields['short_code'].lower()

            if 'country' in fields and fields['country'] is not None:
                currency.country = fields['country'].lower()

            currency.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "currency was updated successfully"
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
        """ Retrieve and delete a currency by id """

        currency = CurrencyModel.query.filter_by(id=id).first()

        try:
            if not currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'currency not found'
                }), 404

            currency.delete()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'currency was deleted successfully'
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
