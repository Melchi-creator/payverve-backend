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
from ..models import (CurrencyModel, KYCModel, UserModel,
                      VirtualAccountNumberModel, WalletModel, db)
from ..services import registration, virtual_account
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

        try:

            if own_wallet and own_wallet.is_active:
                return jsonify({
                    'code': 409,
                    'status_message': 'conflict',
                    'message': 'you already own a wallet with this currency'
                }), 409

            if not own_wallet:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no wallet with this currency to activate'
                }), 404

            kyc_check = KYCModel.query.filter_by(user_id=user_id).first()

            if not kyc_check:
                return jsonify({
                    'code': 409,
                    'status_message': 'unauthorise',
                    'message': 'complete your kyc before proceeding'
                }), 409

            if not compare_digest(str(kyc_check.tier), '3'):
                return jsonify({
                    'code': 409,
                    'status_message': 'unauthorise',
                    'message': 'complete your kyc before proceeding'
                }), 409

            currency = CurrencyModel.query.filter_by(id=currency_id).first()

            if not currency:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'currency not found'
                }), 404

            currency_ticker = currency.short_code.lower()

            # @TODO: integrate foreign virtual account creation with third
            # party here.
            if not compare_digest(currency_ticker, 'ngn'):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'only NGN wallet creation is allowed at the moment'
                }), 403

            # This used to assign own_wallet.account_number, .external_reference
            # and .bank_name, none of which exist any more -- migration
            # 2129b3c36f79 moved them onto virtual_account_numbers. They became
            # throwaway Python attributes, so BellBank issued a real account and
            # Payverve recorded nothing. Same provisioning registration uses.
            try:
                virtual_account.provision_ngn_virtual_account(
                    customer_confirmation, own_wallet, kyc_check.bvn,
                    kyc_check.address, currency_id)
                db.session.commit()
            except registration.RegistrationError as e:
                db.session.rollback()
                return jsonify(e.as_payload()), e.code

            issued = VirtualAccountNumberModel.query.filter_by(
                user_id=user_id, currency_id=currency_id).first()

            NotificationResource.store_nofication(
                title="Wallet Creation",
                body=f"Your {currency_ticker.upper()} wallet is now active. "
                     f"Your account number is "
                     f"{issued.account_number if issued else 'being created'}.",
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
