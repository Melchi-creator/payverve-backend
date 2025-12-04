"""
src/resources/wallet.py
This module defines the WalletResource class, which provides RESTful endpoints for managing wallets.
It includes methods for creating, reading, updating, and deleting wallets, as well as handling errors
related to database operations.
"""
from hmac import compare_digest

from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from .notification import NotificationResource
from ..middlewares import BellbankHelper
from ..models import CurrencyModel, KYCModel, UserModel, WalletModel
from ..utilities import Cryptographer, RandomGenerator, parse_params
from ..value_object import MinimumBalance


class WalletResource(Resource):
    """ WalletResource provides RESTful endpoints for managing wallets """

    @staticmethod
    def ngn_create():
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

            # TODO: integrate real NGN account creation with third party here and remove simulated account number in wallet

            account_number = RandomGenerator.sim_account_number()

            intial_fund = float(0)
            MinimumBalance(intial_fund)
            encrypt_fund = Cryptographer.encrypt(intial_fund)

            external_reference = RandomGenerator.sim_external_ref()

            # noinspection PyArgumentList
            new_wallet = WalletModel(
                fund=encrypt_fund,
                user_id=user_id,
                currency_id=currency_id,
                account_number=account_number,
                is_active=False,
                external_reference=external_reference,
            )
            new_wallet.save()

            NotificationResource.store_nofication(
                title="Wallet Creation",
                body=f"Your NGN wallet has been successfully created with account number {account_number}.",
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

            if own_wallet and own_wallet.is_active:
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

            sim_account_number = RandomGenerator.sim_account_number()
            external_reference = RandomGenerator.sim_external_ref()

            intial_fund = float(0)
            MinimumBalance(intial_fund)
            encrypt_fund = Cryptographer.encrypt(intial_fund)

            currency_ticker = CurrencyModel.query.filter_by(id=currency_id).first().short_code

            # @TODO: integrate foreign virtual account creation (Virtual ccountModel) with third party here and remove simlated account number in wallet

            currency_ticker = currency_ticker.lower()

            if compare_digest(currency_ticker, 'ngn'):
                access_code = BellbankHelper.bellbank_authentication('5')

                response = BellbankHelper.bellbank_virtual_account(
                    access_token=access_code,
                    mobile_number=customer_confirmation.mobile_number,
                    first_name=customer_confirmation.first_name,
                    last_name=customer_confirmation.last_name,
                    address=f"{customer_confirmation.house_number} {customer_confirmation.street_name}, {customer_confirmation.city}, {customer_confirmation.state}, {customer_confirmation.country}",
                    bvn=kyc_check.bvn,
                    gender=customer_confirmation.gender,
                    date_of_birth=str(customer_confirmation.date_of_birth),
                    meta_data={
                        "email_address": customer_confirmation.email_address
                    },
                )

                if not compare_digest(str(response.status_code), '200'):
                    return jsonify({
                        'code': response.status_code,
                        'status_message': 'failed to resolve bank account',
                        'message': response.json().get('message', 'an error occurred while resolving bank account')
                    }), response.status_code

                data = response.json().get('data')
                va_account_number = data.get('accountNumber')

                own_wallet.account_number = va_account_number
                own_wallet.is_active = True
                own_wallet.external_reference = data.get('externalReference')
                own_wallet.save()

            if not compare_digest(currency_ticker, 'ngn'):
                # noinspection PyArgumentList
                new_wallet = WalletModel(
                    fund=encrypt_fund,
                    user_id=user_id,
                    currency_id=currency_id,
                    account_number=sim_account_number,
                    is_active=True,
                    external_reference=external_reference,
                    currency_ticker=currency_ticker
                )
                new_wallet.save()

            NotificationResource.store_nofication(
                title="Wallet Creation",
                body=f"Your {currency_ticker.upper()} wallet has been successfully created with account number {sim_account_number if not compare_digest(currency_ticker, 'ngn') else own_wallet.account_number}.",
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
