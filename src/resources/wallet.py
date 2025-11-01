"""
src/resources/wallet.py
This module defines the WalletResource class, which provides RESTful endpoints for managing wallets.
It includes methods for creating, reading, updating, and deleting wallets, as well as handling errors
related to database operations.
"""
import secrets
from hmac import compare_digest

import requests
from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

import config
from ..models import CurrencyModel, KYCModel, UserModel, VirtualAccountNumberModel, WalletModel
from ..utilities import Cryptographer, RandomGenerator, parse_params
from ..value_object import MinimumBalance


class WalletResource(Resource):
    """ WalletResource provides RESTful endpoints for managing wallets """

    @staticmethod
    def create():
        """ Create a new wallet for a user with a specific currency """

        user_id = request.json.get('user_id')
        currency_id = request.json.get('currency_id')
        email_address = request.json.get('email_address')
        created_by_payverve = request.json.get('created_by_payverve')

        customer_confirmation = UserModel.query.filter_by(id=user_id, email_address=email_address).first()

        if not customer_confirmation:
            return jsonify({
                'code': 404,
                'status_message': 'not found',
                'message': 'user not found'
            }), 404

        if not created_by_payverve:
            return jsonify({
                'code': 403,
                'status_message': 'forbidden',
                'message': 'you are not allowed to create a wallet'
            }), 403

        try:

            wallet_identifier = RandomGenerator.wallet_identifier()

            intial_fund = float(0)
            MinimumBalance(intial_fund)
            encrypt_fund = Cryptographer.encrypt(intial_fund)

            # noinspection PyArgumentList
            new_wallet = WalletModel(
                fund=encrypt_fund,
                wallet_identifier=wallet_identifier,
                user_id=user_id,
                currency_id=currency_id,
                account_number=secrets.randbelow(9000000000) + 1000000000
            )
            new_wallet.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'wallet was successfully created'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'a wallet with this currency has already been listed'
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

    @staticmethod
    def create_public():
        """ Create a new wallet for a user with a specific currency """

        user_id = request.json.get('user_id')
        currency_id = request.json.get('currency_id')

        customer_confirmation = UserModel.query.filter_by(id=user_id).first()

        if not customer_confirmation:
            return jsonify({
                'code': 404,
                'status_message': 'not found',
                'message': 'user not found'
            }), 404

        own_wallet = WalletModel.query.filter_by(user_id=user_id, currency_id=currency_id).first()

        try:

            ngn_currency_id = CurrencyModel.query.filter_by(short_code='ngn').first().id

            if own_wallet and not compare_digest(str(ngn_currency_id), str(currency_id)):
                return jsonify({
                    'code': 409,
                    'status_message': 'conflict',
                    'message': 'you already own a wallet with this currency'
                }), 409

            if currency_id == ngn_currency_id and own_wallet.is_active:
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you can only create one ngn wallet'
                }), 403

            kyc_check = KYCModel.query.filter_by(user_id=user_id).first()

            if not kyc_check.bvn_present or not kyc_check.nin_present:
                return jsonify({
                    'code': 409,
                    'status_message': 'unauthorise',
                    'message': 'complete your kyc before proceeding'
                }), 409

            token = request.headers.get('Authorization').split(" ")[1]

            response = None

            if not  compare_digest(str(ngn_currency_id), str(currency_id)):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'the currency id used is not the ngn currency id'
                }), 400

            if compare_digest(str(ngn_currency_id), str(currency_id)):

                headers = {
                    'content-type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }

                payload = {
                    'email_address': customer_confirmation.email_address,
                    'mobile_number': customer_confirmation.mobile_number,
                    'first_name': customer_confirmation.first_name,
                    'last_name': customer_confirmation.last_name,
                    'bvn': kyc_check.bvn,
                }

                response = requests.request("POST",
                                            f'{config.app_path}/flutterwave-create-ngn',
                                            headers=headers,
                                            json=payload)

                if response.status_code != 200:
                    return jsonify({
                        'code': response.status_code,
                        'status_message': 'failed',
                        'message': 'could not create wallet at the moment, try again later'
                    }), response.status_code

            wallet_identifier = RandomGenerator.wallet_identifier()

            intial_fund = float(0)
            MinimumBalance(intial_fund)
            encrypt_fund = Cryptographer.encrypt(intial_fund)

            final_response = response.json()
            outer_data = final_response.get('data', {})
            inner_data = outer_data.get('data', {})
            account_number = inner_data.get('account_number')
            bank_name = inner_data.get('bank_name')

            # # @TODO thia following block of code will be removed
            # if config.env == 'dev':
            #     code = str(secrets.randbelow(10 ** 5)).zfill(5)
            #     account_number = str(code) + str(account_number)[-5:]

            currency_ticker = CurrencyModel.query.filter_by(id=currency_id).first().short_code

            if compare_digest(str(ngn_currency_id), str(currency_id)) and not own_wallet.is_active:
                own_wallet.is_active = True
                own_wallet.account_number = account_number
                own_wallet.bank_name = bank_name
                own_wallet.save()

                # noinspection PyArgumentList
                new_virtual_ngn_account = VirtualAccountNumberModel(
                    response_code=inner_data.get('response_code'),
                    response_status_message=inner_data.get('response_status_message'),
                    flw_ref=inner_data.get('flw_ref'),
                    order_ref=inner_data.get('order_ref'),
                    frequency=inner_data.get('frequency'),
                    created_at_by_flw=inner_data.get('created_at'),
                    expiry_date=inner_data.get('expiry_date'),
                    account_number=account_number,
                    bank_name=bank_name,
                    note=inner_data.get('note'),
                    amount=inner_data.get('amount'),
                    currency_ticker=currency_ticker,
                    user_id=user_id,
                    currency_id=currency_id
                )
                new_virtual_ngn_account.save()

                return jsonify({
                    'code': 200,
                    'status_message': 'success',
                    'message': 'ngn wallet created successfully and activated'
                }), 200

            # noinspection PyArgumentList
            new_wallet = WalletModel(
                fund=encrypt_fund,
                wallet_identifier=wallet_identifier,
                user_id=user_id,
                currency_id=currency_id,
                account_number=account_number,
                bank_name=bank_name,
                is_active=True,
                currency_ticker=currency_ticker
            )
            new_wallet.save()

            # noinspection PyArgumentList
            new_virtual_ngn_account = VirtualAccountNumberModel(
                response_code=inner_data.get('response_code'),
                response_status_message=inner_data.get('response_status_message'),
                flw_ref=inner_data.get('flw_ref'),
                order_ref=inner_data.get('order_ref'),
                frequency=inner_data.get('frequency'),
                created_at_by_flw=inner_data.get('created_at'),
                expiry_date=inner_data.get('expiry_date'),
                account_number=account_number,
                bank_name=bank_name,
                note=inner_data.get('note'),
                amount=inner_data.get('amount'),
                currency_ticker=currency_ticker,
                user_id=user_id,
                currency_id=currency_id
            )
            new_virtual_ngn_account.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'wallet was successfully created'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'a wallet with this currency has already been listed'
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

    @staticmethod
    def read_all():
        """ Retrieve all wallets """

        wallets = WalletModel.query.order_by(WalletModel.user_id.desc()).all()

        try:
            if not wallets:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no wallet was found'
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
                    'account_number': wallet.account_number,
                    'bank_name': wallet.bank_name,
                    'is_active': wallet.is_active,
                    'created_at': wallet.created_at,
                    'updated_at': wallet.updated_at
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
        """ Retrieve a wallet by id """

        wallet = WalletModel.query.filter_by(id=id).first()

        try:
            if not wallet:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no wallet was found'
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
                'account_number': wallet.account_number,
                'bank_name': wallet.bank_name,
                'is_active': wallet.is_active,
                'created_at': wallet.created_at,
                'updated_at': wallet.updated_at
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
    def read_all_user(id=None):
        """ Retrieve all wallets """

        wallets = WalletModel.query.filter_by(user_id=id).all()

        try:
            if not wallets:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no wallet was found'
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
                    'account_number': wallet.account_number,
                    'bank_name': wallet.bank_name,
                    'is_active': wallet.is_active,
                    'created_at': wallet.created_at,
                    'updated_at': wallet.updated_at
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
                    'status_message': 'data not found',
                    'message': 'no wallet was found'
                }), 404

            MinimumBalance(fund)
            decrypt_fund = Cryptographer.decrypt(wallet.fund)

            fund = float(decrypt_fund) + fund
            encrypt_fund = Cryptographer.encrypt(fund)

            wallet.fund = encrypt_fund
            wallet.save()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'wallet was successfully updated'
            }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'a wallet with this currency has already been listed'
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
