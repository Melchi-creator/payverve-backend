"""
payverve_transfer.py

Defines all functions for payverve transfer especially CRUD
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
from ..models import CurrencyModel, PayverveTransferModel, UserModel, WalletModel
from ..utilities import RandomGenerator, parse_params


class PayverveTransferResource(Resource):
    """ This class is concern with Transfer within Payverve Resources """

    @staticmethod
    @parse_params(
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=True),
        Argument("account", location="json", required=True),
        Argument("user", location="json", required=True),
        Argument("wallet", location="json", required=True),
    )
    def create(amount, narration, account, user, wallet):
        """ Payverve Transfer """

        try:
            if len(account) > 10 or len(account) < 10:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'the account number is not correct'
                }), 400

            recipient = WalletModel.query.filter_by(account_number=account).first()
            sender_currency = WalletModel.query.filter_by(id=wallet).first()
            payverve_transfers = PayverveTransferModel.query.all()

            check_currency = None

            if recipient:
                check_currency = CurrencyModel.query.filter_by(id=recipient.currency).first()

            sender = WalletModel.query.filter_by(user=user, currency=check_currency.id).first()

            if not recipient:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'the recipient account number was not found'
                }), 404

            if not sender_currency:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'the sender wallet does not exist'
                }), 404

            if not sender:
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': f'the sender doesn\'t have a {check_currency.short_code} account'
                }), 404

            if str(sender_currency.currency) != str(recipient.currency):
                return jsonify({
                    'code': 404,
                    'code_message': 'not found',
                    'data': 'the sender account currency doesn\'t match recipient currency'
                }), 404

            if str(recipient.user) == str(sender.user):
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'you can\'t transfer between different currencies, swap instead'
                }), 400

            if float(amount) > sender.fund:
                return jsonify({
                    'code': 400,
                    'code_message': 'bad request',
                    'data': 'your balance is not up to the inputted amount'
                }), 400

            sender.fund -= float(amount)
            recipient.fund += float(amount)

            reference_number = RandomGenerator.payverve_transfer_reference_number()

            for one_payverve_transfer in payverve_transfers:
                if str(one_payverve_transfer.reference) == str(reference_number):
                    reference_number = RandomGenerator.payverve_transfer_reference_number()

            transfer_currency = check_currency.short_code.upper()

            # noinspection PyArgumentList
            new_payverve_transfer = PayverveTransferModel(
                amount=amount,
                narration=narration,
                account=account,
                reference=reference_number,
                transfer_pair=f'Wallet({transfer_currency})-Wallet({transfer_currency})',
                user=user,
                wallet=wallet,
            )
            sender.save()
            recipient.save()
            new_payverve_transfer.save()

            user = UserModel.query.filter_by(id=recipient.user).first()

            data = {
                'id': new_payverve_transfer.id,
                'amount': new_payverve_transfer.amount,
                'narration': new_payverve_transfer.narration,
                'account': new_payverve_transfer.account,
                'account_extra': f'{user.first_name} {user.last_name}',
                'reference': new_payverve_transfer.reference,
                'transaction_type': new_payverve_transfer.transaction_type,
                'transfer_pair': new_payverve_transfer.transfer_pair,
                'user': new_payverve_transfer.user,
                'wallet': new_payverve_transfer.wallet,
                'created_at': new_payverve_transfer.created_at,
                'updated_at': new_payverve_transfer.updated_at
            }

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': {
                    'data': 'money transfered successfully',
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
        """ Retrieve all payverve transfer """

        payverve_transfers = PayverveTransferModel.query.all()

        try:
            if not payverve_transfers:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no payverve transfer was found'
                }), 404

            data = []

            for payverve_transfer in payverve_transfers:
                recipient = WalletModel.query.filter_by(account_number=payverve_transfer.account).first()
                user = UserModel.query.filter_by(id=recipient.user).first()
                data.append({
                    'id': payverve_transfer.id,
                    'amount': payverve_transfer.amount,
                    'narration': payverve_transfer.narration,
                    'account': payverve_transfer.account,
                    'account_extra': f'{user.first_name} {user.last_name}',
                    'reference': payverve_transfer.reference,
                    'transaction_type': payverve_transfer.transaction_type,
                    'transfer_pair': payverve_transfer.transfer_pair,
                    'user': payverve_transfer.user,
                    'wallet': payverve_transfer.wallet,
                    'created_at': payverve_transfer.created_at,
                    'updated_at': payverve_transfer.updated_at
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
        """ Retrieve one payverve transfer by id """

        payverve_transfer = PayverveTransferModel.query.filter_by(id=id).first()

        try:
            if not payverve_transfer:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no payverve transfer was found'
                }), 404

            recipient = WalletModel.query.filter_by(account_number=payverve_transfer.account).first()
            user = UserModel.query.filter_by(id=recipient.user).first()
            data = {
                'id': payverve_transfer.id,
                'amount': payverve_transfer.amount,
                'narration': payverve_transfer.narration,
                'account': payverve_transfer.account,
                'account_extra': f'{user.first_name} {user.last_name}',
                'reference': payverve_transfer.reference,
                'transaction_type': payverve_transfer.transaction_type,
                'transfer_pair': payverve_transfer.transfer_pair,
                'user': payverve_transfer.user,
                'wallet': payverve_transfer.wallet,
                'created_at': payverve_transfer.created_at,
                'updated_at': payverve_transfer.updated_at
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
        """ Retrieve and delete one payverve tranfer by id """

        payverve_transfer = PayverveTransferModel.query.filter_by(id=id).first()

        try:
            if not payverve_transfer:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no payverve transfer was found'
                }), 404

            payverve_transfer.delete()

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
