"""
wallet.py

Defines all functions for wallet especially CRUD
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

from ..models import CurrencyModel, WalletModel
from ..utilities import RandomGenerator, parse_params


class WalletResource(Resource):
    """ This class is concern with Wallet Resources """

    @staticmethod
    @parse_params(
        Argument("user", location="json", required=True),
        Argument("currency", location="json", required=True),
    )
    def create(user, currency):
        """ Adds a new wallet """

        wallets = WalletModel.query.filter_by(user=user).all()

        try:
            for wallet in wallets:
                if currency in str(wallet.currency):
                    return jsonify({
                        'code': 409,
                        'code_status': 'conflict',
                        'data': 'you alread own this currency'
                    }), 409

            # noinspection PyArgumentList
            new_wallet = WalletModel(
                fund=0,
                account_number=RandomGenerator.wallet_account_number(),
                user=user,
                currency=currency
            )
            new_wallet.save()

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
        """ Retrieve all wallets """

        wallets = WalletModel.query.all()

        try:
            if not wallets:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no wallet was found'
                }), 404

            data = []

            for wallet in wallets:
                currency = CurrencyModel.query.filter_by(id=wallet.currency).first()
                data.append({
                    'id': wallet.id,
                    'fund': wallet.fund,
                    'account_number': wallet.account_number,
                    'user': wallet.user,
                    'currency': wallet.currency,
                    'currency_extras': {
                        'currency_shortcode': currency.short_code,
                        'currency_full_name': currency.name,
                    },
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

            currency = CurrencyModel.query.filter_by(id=wallet.currency).first()
            data = {
                'id': wallet.id,
                'fund': wallet.fund,
                'account_number': wallet.account_number,
                'user': wallet.user,
                'currency': wallet.currency,
                'currency_extras': {
                    'currency_shortcode': currency.short_code,
                    'currency_full_name': currency.name,
                },
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
        Argument("fund", location="json"),
    )
    def update(id=None, **fields):
        """ Updates a wallet by id """

        wallet = WalletModel.query.filter_by(id=id).first()

        try:
            if not wallet:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no wallet was found'
                }), 404

            if 'fund' in fields and fields['fund'] is not None:
                wallet.fund = fields['fund']

            wallet.save()

            currency = CurrencyModel.query.filter_by(id=wallet.currency).first()
            data = {
                'id': wallet.id,
                'fund': wallet.fund,
                'account_number': wallet.account_number,
                'user': wallet.user,
                'currency': wallet.currency,
                'currency_extras': {
                    'currency_shortcode': currency.short_code,
                    'currency_full_name': currency.name,
                },
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

        wallet = WalletModel.query.filter_by(id=id).first()
        user_wallets = WalletModel.query.filter_by(user=wallet.user).all()

        currency = CurrencyModel.query.filter_by(id=wallet.currency).first()

        try:
            if not wallet:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
                }), 404

            if currency.short_code == 'ngn':
                return jsonify({
                    'code': 403,
                    'code_status': 'forbidden',
                    'data': 'you can\'t delete your default wallet'
                }), 403

            if wallet.fund > 0:
                for user_wallet in user_wallets:
                    currency = CurrencyModel.query.filter_by(short_code='ngn').first()
                    if str(user_wallet.currency) == str(currency.id):
                        # Doghor - remember to include conversion rate when adding funds to naira account
                        user_wallet.fund += wallet.fund
                        user_wallet.save()
                        break

            wallet.delete()

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
