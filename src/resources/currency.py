"""
currency.py

Defines all functions for currency especially CRUD
"""
from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    SQLAlchemyError, ProgrammingError

from ..models import CurrencyModel
from ..utilities import parse_params


class CurrencyResource(Resource):
    """ This class is concern with User Resources """

    @staticmethod
    @parse_params(
        Argument("name", location="json", required=True),
        Argument("short_code", location="json", required=True),
        Argument("country", location="json", required=True),
    )
    def create(name, short_code, country):
        """ Adds a new currency """

        currencies = CurrencyModel.query.all()

        try:
            for currency in currencies:
                if name in currency.name or short_code in currency.short_code or country in currency.country:
                    return jsonify({
                        'code': 409,
                        'code_status': 'conflict',
                        'data': 'this currency has already been listed'
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

    @staticmethod
    def read_all():
        """ Retrieve all currencies """

        currencies = CurrencyModel.query.all()

        try:
            if not currencies:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no currency was found'
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
        """ Retrieve a currency by id """

        currency = CurrencyModel.query.filter_by(id=id).first()

        try:
            if not currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no currency was found'
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
                    'data': 'no currency was found'
                }), 404

            if 'name' in fields and fields['name'] is not None:
                currency.name = fields['name'].lower()

            if 'short_code' in fields and fields['short_code'] is not None:
                currency.short_code = fields['short_code'].lower()

            if 'country' in fields and fields['country'] is not None:
                currency.country = fields['country'].lower()

            currency.save()

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
    def delete(id=None):
        """ Retrieve and delete a currency by id """

        currency = CurrencyModel.query.filter_by(id=id).first()

        try:
            if not currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
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
