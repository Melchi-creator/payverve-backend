"""
src/resources/wallet.py
This module defines the WalletResource class, which provides RESTful endpoints for managing wallets.
It includes methods for creating, reading, updating, and deleting wallets, as well as handling errors
related to database operations.
"""
from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..models import WalletModel
# from ..utilities import RandomGenerator, emailHandler, parse_params
from ..utilities import Cryptographer, RandomGenerator, parse_params
from ..value_object import MinimumBalance


class WalletResource(Resource):
    """ WalletResource provides RESTful endpoints for managing wallets """

    @staticmethod
    def create():
        """ Create a new wallet for a user with a specific currency """

        user_id = request.json.get('user_id')
        currency_id = request.json.get('currency_id')

        wallets = WalletModel.query.filter_by(user_id=user_id).all()

        try:

            for wallet in wallets:
                if currency_id in str(wallet.currency_id):
                    return jsonify({
                        'code': 409,
                        'code_status': 'conflict',
                        'data': 'you already own a wallet with this currency'
                    }), 409

            wallet_identifier = RandomGenerator.wallet_identifier()

            intial_fund = float(0)
            MinimumBalance(intial_fund)
            encrypt_fund = Cryptographer.encrypt(intial_fund)

            # noinspection PyArgumentList
            new_wallet = WalletModel(
                fund=encrypt_fund,
                wallet_identifier=wallet_identifier,
                user_id=user_id,
                currency_id=currency_id
            )
            new_wallet.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'wallet was successfully created'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'data': 'a wallet with this currency has already been listed'
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
        """ Retrieve all wallets """

        wallets = WalletModel.query.order_by(WalletModel.user_id.desc()).all()

        try:
            if not wallets:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no wallet was found'
                }), 404

            data = []

            for wallet in wallets:
                data.append({
                    'id': wallet.id,
                    'fund': float(Cryptographer.decrypt(wallet.fund)),
                    'wallet_identifier': wallet.wallet_identifier,
                    'user_id': wallet.user_id,
                    'user_name': wallet.users.first_name + ' ' + wallet.users.last_name,
                    'currency_id': wallet.currency_id,
                    'currency_extras': {
                        'currency_shortcode': wallet.currencies.short_code,
                        'currency_full_name': wallet.currencies.name,
                    },
                    'created_at': wallet.created_at,
                    'updated_at': wallet.updated_at
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

        wallet = WalletModel.query.filter_by(id=id).first()

        try:
            if not wallet:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no wallet was found'
                }), 404

            data = {
                'id': wallet.id,
                'fund': float(Cryptographer.decrypt(wallet.fund)),
                'wallet_identifier': wallet.wallet_identifier,
                'user_id': wallet.user_id,
                'user_name': wallet.users.first_name + ' ' + wallet.users.last_name,
                'currency_id': wallet.currency_id,
                'currency_extras': {
                    'currency_shortcode': wallet.currencies.short_code,
                    'currency_full_name': wallet.currencies.name,
                },
                'created_at': wallet.created_at,
                'updated_at': wallet.updated_at
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
    def read_all_user(id=None):
        """ Retrieve all wallets """

        wallets = WalletModel.query.filter_by(user_id=id).all()

        try:
            if not wallets:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no wallet was found'
                }), 404

            data = []

            for wallet in wallets:
                data.append({
                    'id': wallet.id,
                    'fund': float(Cryptographer.decrypt(wallet.fund)),
                    'wallet_identifier': wallet.wallet_identifier,
                    'user_id': wallet.user_id,
                    'user_name': wallet.users.first_name + ' ' + wallet.users.last_name,
                    'currency_id': wallet.currency_id,
                    'currency_extras': {
                        'currency_shortcode': wallet.currencies.short_code,
                        'currency_full_name': wallet.currencies.name,
                    },
                    'created_at': wallet.created_at,
                    'updated_at': wallet.updated_at
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
    @parse_params(
        Argument('fund', type=int, required=True, location='json'),
    )
    def update(fund, id=None):
        """ Update a wallet's fund """

        try:

            wallet = WalletModel.query.filter_by(id=id).first()

            if not wallet:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no wallet was found'
                }), 404

            MinimumBalance(fund)
            decrypt_fund = Cryptographer.decrypt(wallet.fund)

            fund = float(decrypt_fund) + fund
            encrypt_fund = Cryptographer.encrypt(fund)

            wallet.fund = encrypt_fund
            wallet.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'wallet was successfully updated'
            }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'data': 'a wallet with this currency has already been listed'
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
