"""
local_transfer.py

Defines all functions for swapping currency especially CRUD
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

from .. import config
from ..models import CurrencyModel, ExchangeRateModel, LocalTransferModel, WalletModel
from ..utilities import RandomGenerator, parse_params


class LocalTransferResource(Resource):
    """ This class is concern with Local Transfer Resources """

    @staticmethod
    @parse_params(
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=True),
        Argument("account", location="json", required=True),
        Argument("name", location="json", required=True),
        Argument("bank", location="json", required=True),
        Argument("user", location="json", required=True),
        Argument("wallet", location="json", required=True),
    )
    def create(amount, narration, account, name, bank, user, wallet):
        """ Swap Currency """

        try:
            local_transfers = LocalTransferModel.query.all()

            check_balance = WalletModel.query.filter_by(id=wallet, user=user).first()

            if not check_balance:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'could not find the wallet'
                }), 404

            if float(amount) > check_balance.fund:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'your balance is not up to the inputted amount'
                }), 400

            # TODO: Check which currency is the recipient curreny
            # TODO: Verify recipient account and send moeny to it via paystack

            check_balance.fund -= float(amount)

            reference_number = RandomGenerator.local_transfer_reference_number()

            for local_transfer in local_transfers:
                if str(local_transfer.rference_number) == str(reference_number):
                    reference_number = RandomGenerator.local_transfer_reference_number()

            wallet_model = WalletModel.query.filter_by(id=wallet).first()
            curreny = CurrencyModel.query.filter_by(id=wallet_model.currency).first()

            transfer_type = f'local tranfer (Payverve - {bank}) - {curreny.short_code}'

            # noinspection PyArgumentList
            new_local_transfer = LocalTransferModel(
                amount=amount,
                narration=narration,
                account=account,
                name=name,
                bank=bank,
                rference_number=reference_number,
                user=user,
                wallet=wallet,
                transfer_type=transfer_type
            )
            new_local_transfer.save()

            data = {
                'id': new_local_transfer.id,
                'amount': new_local_transfer.amount,
                'narration': new_local_transfer.narration,
                'account': new_local_transfer.account,
                'name': new_local_transfer.name,
                'bank': new_local_transfer.bank,
                'reference': new_local_transfer.rference_number,
                'transfer_type': new_local_transfer.transfer_type,
                'user': new_local_transfer.user,
                'wallet': new_local_transfer.wallet,
                'created_at': new_local_transfer.created_at,
                'updated_at': new_local_transfer.updated_at
            }

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': {
                    'data': 'transfer was done successfully',
                    'details': data
                }
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

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'code_status': 'calculation error - arithmetic, value, zerodivision error',
                'data': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieve all local transfers """

        local_transfers = LocalTransferModel.query.all()

        try:
            if not local_transfers:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no local transfer history was found'
                }), 404

            data = []

            for local_transfer in local_transfers:
                data.append({
                    'id': local_transfer.id,
                    'amount': local_transfer.amount,
                    'narration': local_transfer.narration,
                    'account': local_transfer.account,
                    'name': local_transfer.name,
                    'bank': local_transfer.bank,
                    'reference': local_transfer.rference_number,
                    'transfer_type': local_transfer.transfer_type,
                    'user': local_transfer.user,
                    'wallet': local_transfer.wallet,
                    'created_at': local_transfer.created_at,
                    'updated_at': local_transfer.updated_at
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
        """ Retrieve one swapped currency by id """

        swapped_currency = LocalTransferModel.query.filter_by(id=id).first()

        try:
            if not swapped_currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no swapped currency was found'
                }), 404

            data = {
                'id': swapped_currency.id,
                'base_currency': swapped_currency.base_currency,
                'target_currency': swapped_currency.target_currency,
                'amount': swapped_currency.amount,
                'transaction_type': swapped_currency.transaction_type,
                'currency_pair': swapped_currency.currency_pair,
                'amount_received': swapped_currency.amount_received,
                'reference': swapped_currency.reference,
                'user': swapped_currency.user,
                'created_at': swapped_currency.created_at,
                'updated_at': swapped_currency.updated_at
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
        """ Retrieve and delete one swapped currency by id """

        swapped_currency = LocalTransferModel.query.filter_by(id=id).first()

        try:
            if not swapped_currency:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no swapped currency was found'
                }), 404

            swapped_currency.delete()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'swap history was deleted successfully'
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
