"""
src/resources/wallet.py
This module defines the WalletResource class, which provides RESTful endpoints for managing wallets.
It includes methods for creating, reading, updating, and deleting wallets, as well as handling errors
related to database operations.
"""
import secrets
from datetime import datetime
from hmac import compare_digest

from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

import config
from .notification import NotificationResource
from ..middlewares import BellbankHelper, FlutterwaveHelper
from ..models import CurrencyModel, KYCModel, UserModel, VirtualAccountNumberModel, WalletModel
from ..utilities import Cryptographer, RandomGenerator, decode_token, parse_params
from ..value_object import MinimumBalance


class WalletResource(Resource):
    """ WalletResource provides RESTful endpoints for managing wallets """

    @staticmethod
    def ngn_create():
        """ Create a new wallet for a user with a specific currency """

        data = request.get_json()

        user_id = data.get('user_id')
        currency_id = data.get('currency_id')
        email_address = data.get('email_address')
        created_by_payverve = data.get('created_by_payverve')

        customer_confirmation = UserModel.query.filter_by(
            id=user_id, email_address=email_address).first()

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

            intial_fund = float(0)
            MinimumBalance(intial_fund)
            encrypt_fund = Cryptographer.encrypt(intial_fund)

            # noinspection PyArgumentList
            new_wallet = WalletModel(
                fund=encrypt_fund,
                user_id=user_id,
                currency_id=currency_id,
            )
            new_wallet.save()

            NotificationResource.store_nofication(
                title="Wallet Creation",
                body=f"Your NGN wallet has been successfully created.",
                user_id=user_id,
            )

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
    def other_wallet():
        """ Create a new wallet for a user with a specific currency """

        data = request.get_json()
        user_id = data.get('user_id')
        currency_id = data.get('currency_id')

        customer_confirmation = UserModel.query.filter_by(id=user_id).first()

        if not customer_confirmation:
            return jsonify({
                'code': 404,
                'status_message': 'not found',
                'message': 'user not found'
            }), 404

        own_wallet = WalletModel.query.filter_by(
            user_id=user_id, currency_id=currency_id).first()

        if not own_wallet:
            return jsonify({
                'code': 404,
                'status_message': 'not found',
                'message': 'wallet record not found - ensure ngn_create ran at signup'
            }), 404

        try:

            if own_wallet.is_active:
                return jsonify({
                    'code': 409,
                    'status_message': 'conflict',
                    'message': 'you already own a wallet with this currency'
                }), 409

            kyc_check = KYCModel.query.filter_by(user_id=user_id).first()

            if not compare_digest(str(kyc_check.tier), '3'):
                return jsonify({
                    'code': 409,
                    'status_message': 'unauthorise',
                    'message': 'complete your kyc before proceeding'
                }), 409

            currency_ticker = CurrencyModel.query.filter_by(
                id=currency_id).first().short_code
            currency_ticker = currency_ticker.lower()

            if not compare_digest(currency_ticker, 'ngn'):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'only NGN wallet creation is allowed at the moment'
                }), 403

            access_token = FlutterwaveHelper.flutterwave_authentication()

            # find or create the Flutterwave customer
            search_response = FlutterwaveHelper.search_for_customer(
                access_token, customer_confirmation.email_address
            )
            search_data = search_response.json()

            customer_id = None
            results = search_data.get('data') or []
            if results:
                customer_id = results[0].get('id')

            if not customer_id:
                create_response = FlutterwaveHelper.create_flutterwave_account(
                    access_token=access_token,
                    email_address=customer_confirmation.email_address,
                    mobile_number=customer_confirmation.mobile_number,
                    first_name=customer_confirmation.first_name,
                    last_name=customer_confirmation.last_name,
                )

                if not compare_digest(str(create_response.status_code), '200') and \
                        not compare_digest(str(create_response.status_code), '201'):
                    return jsonify({
                        'code': create_response.status_code,
                        'status_message': 'failed to create customer',
                        'message': create_response.json().get('message', 'an error occurred while creating customer')
                    }), create_response.status_code

                customer_id = create_response.json().get('data', {}).get('id')

            reference_number = secrets.token_urlsafe(16)

            va_response = FlutterwaveHelper.virtual_account(
                access_token=access_token,
                reference_number=reference_number,
                customer_id=customer_id,
                email_address=customer_confirmation.email_address,
                short_code=currency_ticker,
                user_datails=customer_confirmation,
                kyc_check=kyc_check,
            )

            if not compare_digest(str(va_response.status_code), '200') and \
                    not compare_digest(str(va_response.status_code), '201'):
                return jsonify({
                    'code': va_response.status_code,
                    'status_message': 'failed to resolve bank account',
                    'message': va_response.json().get('message', 'an error occurred while resolving bank account')
                }), va_response.status_code

            va_data = va_response.json().get('data')

            own_wallet.account_number = va_data.get('account_number')
            own_wallet.bank_name = va_data.get(
                'account_bank_name')   # was: va_data.get('bank_name')
            own_wallet.external_reference = va_data.get(
                'reference') or reference_number
            own_wallet.flutterwave_account_id = va_data.get('id')
            own_wallet.is_active = True
            own_wallet.save()

            NotificationResource.store_nofication(
                title="Wallet Creation",
                body=f"Your {currency_ticker.upper()} wallet has been successfully created with account number {own_wallet.account_number}.",
                user_id=user_id,
            )

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
                    'user_id': wallet.user_id,
                    'user_name': wallet.users.first_name + ' ' + wallet.users.last_name,
                    'currency_id': wallet.currency_id,
                    'currency_extras': {
                        'currency_shortcode': wallet.currencies.short_code,
                        'currency_full_name': wallet.currencies.name,
                    },
                    'account_number': wallet.account_number,
                    'bank_name': wallet.bank_name,
                    'flutterwave_account_id': wallet.flutterwave_account_id,
                    'is_active': wallet.is_active,
                    'created_at': wallet.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': wallet.updated_at.strftime("%d %b %Y, %I:%M %p") if wallet.updated_at else None,
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
                'created_at': wallet.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': wallet.updated_at.strftime("%d %b %Y, %I:%M %p") if wallet.updated_at else None,
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
                    'created_at': wallet.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': wallet.updated_at.strftime("%d %b %Y, %I:%M %p") if wallet.updated_at else None,
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
