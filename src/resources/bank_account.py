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

from ..models import BankAccountModel
from ..utilities import parse_params


class BankAccountResource(Resource):
    @staticmethod
    @parse_params(
        Argument("bankname", location="json", required=True),
        Argument("account_number", location="json", required=True),
        Argument("bank_swift", location="json", required=True),
        Argument("account_first_name", location="json", required=True),
        Argument("account_last_name", location="json", required=True),
        Argument("country", location="json", required=True),
    )
    def create(bankname, account_number, bank_swift, account_first_name, account_last_name, country):
        """ Adds a new bank account """

        bank_accounts = BankAccountModel.query.all()

        try:
            for account in bank_accounts:
                if bankname in account.bank_name or account_number in account.account_number:
                    return jsonify({
                        'code': 409,
                        'code_status': 'conflict',
                        'data': 'this bank account exists'
                    }), 409

            # noinspection PyArgumentList
            new_bank_account = BankAccountModel(
                bankname=bankname.lower(),
                account_number=account_number,
                bank_swift=bank_swift,
                account_first_name=account_first_name.lower(),
                account_last_name=account_last_name.lower(),
                country=country.lower(),
            )
            new_bank_account.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'bank account was successfully added'
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

        bank_accounts = BankAccountModel.query.all()

        try:
            if not bank_accounts:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no account was found'
                }), 404

            data = []

            for bank_account in bank_accounts:
                data.append({
                    'id': bank_account.id,
                    'bankname': bank_account.bankname,
                    'account_number': bank_account.account_number,
                    'bank_swifts': bank_account.bank_swift,
                    'account_first_name': bank_account.account_first_name,
                    'account_last_name': bank_account.account_last_name,
                    'country': bank_account.country,
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
        """ Retrieve a bank account by id """

        bank_accounts = BankAccountModel.query.filter_by(id=id).first()

        try:
            if not bank_accounts:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no account was found'
                }), 404

            data = {
                'id': bank_accounts.id,
                'bankname': bank_accounts.bankname,
                'account_number': bank_accounts.account_number,
                'bank_swifts': bank_accounts.bank_swift,
                'account_first_name': bank_accounts.account_first_name,
                'account_last_name': bank_accounts.account_last_name,
                'country': bank_accounts.country,
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
        Argument("bankname", location="json", required=True),
        Argument("account_number", location="json", required=True),
        Argument("bank_swift", location="json", required=True),
        Argument("account_first_name", location="json", required=True),
        Argument("account_last_name", location="json", required=True),
        Argument("country", location="json", required=True),
    )
    def update(id=None, **fields):
        """ Updates a bank account detail by id """

        bank_accounts = BankAccountModel.query.filter_by(id=id).first()

        try:
            if not bank_accounts:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no bank account was found'
                }), 404

            if 'bankname' in fields and fields['bankname'] is not None:
                bank_accounts.bankname = fields['bankname'].lower()

            if 'account_number' in fields and fields['account_number'] is not None:
                bank_accounts.account_number = fields['account_number']

            if 'account_first_name' in fields and fields['account_first_name'] is not None:
                bank_accounts.account_first_name = fields['account_first_name'].lower()

            if 'account_last_name' in fields and fields['account_last_name'] is not None:
                bank_accounts.account_las_namet = fields['account_last_name'].lower()

            if 'country' in fields and fields['country'] is not None:
                bank_accounts.country = fields['country'].lower()

            bank_accounts.save()

            data = {
                'id': bank_accounts.id,
                'bankname': bank_accounts.bankname,
                'account_number': bank_accounts.account_number,
                'bank_swifts': bank_accounts.bank_swift,
                'account_first_name': bank_accounts.account_first_name,
                'account_last_name': bank_accounts.account_last_name,
                'country': bank_accounts.country,
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

        bank_accounts = BankAccountModel.query.filter_by(id=id).first()

        try:
            if not bank_accounts:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no user account was found'
                }), 404

            bank_accounts.delete()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': 'account was deleted successfully'
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
