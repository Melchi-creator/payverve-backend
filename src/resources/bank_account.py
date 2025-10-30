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

from ..middlewares import PaystackHelper
from ..models import BankAccountModel, KYCModel, UserModel
from ..utilities import Cryptographer, parse_params


class BankAccountResource(Resource):
    @staticmethod
    @parse_params(
        Argument('bank_name', location='json', required=True),
        Argument('bank_code', location='json', required=True),
        Argument('account_number', location='json', required=True),
        Argument('user_id', location='json', required=True),
    )
    def create(bank_name, bank_code, account_number, user_id):
        """ Adds a new bank account """

        try:

            customer = UserModel.query.filter_by(id=user_id).first()

            if not customer:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'Customer not found'
                }), 404

            # @TODO: Know your customer

            existing_kyc = KYCModel.query.filter_by(user_id=user_id).first()

            if not existing_kyc or existing_kyc.bvn is None:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'You need to complete your KYC before adding bank account details'
                }), 400

            number_of_account = BankAccountModel.query.filter_by(user_id=user_id).count()

            if number_of_account >= 2:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'You can only add two bank account details'
                }), 400

            bank_detail = BankAccountModel.query.filter_by(user_id=user_id,
                                                           account_number=account_number).first()

            if bank_detail:
                return jsonify({
                    'code': 409,
                    'status_message': 'conflict',
                    'message': 'You\'ve already added this bank account details'
                }), 409

            response = PaystackHelper.verify_bank(account_number, bank_code)

            if response.status_code != 200:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'bank addition failed'
                }), 400

            bank_verified = response.json()['data']
            verified_list = bank_verified['account_name'].split(' ')

            first_name = customer.first_name.upper()
            last_name = customer.last_name.upper()

            if first_name not in verified_list or last_name not in verified_list:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'The account name does not match the account number'
                }), 400

            get_bank = PaystackHelper.paystack_bank('/bank', "GET")
            get_bank_data = get_bank.json()['data']

            country_name = None
            currency = None

            for fetch_bank_code in get_bank_data:
                if fetch_bank_code['code'] == bank_code:
                    country_name = fetch_bank_code['country']
                    currency = fetch_bank_code['currency']
                    break

            get_country = PaystackHelper.paystack_bank('/country', "GET")
            get_country_data = get_country.json()['data']

            iso_code_digit = None

            for country_code in get_country_data:
                if country_code['name'] == country_name:
                    iso_code_digit = country_code['iso_code']
                    break

            account_type = 'personal'

            # @TODO: Implement Paystack account verifcation that works on live alone
            # https://paystack.com/docs/identity-verification/validate-customer/#bank-account-validation
            #
            # data = {
            #     'account_name': first_name + ' ' + last_name,
            #     'account_number': account_number,
            #     'account_type': account_type,
            #     'bank_code': bank_code,
            #     'country_code': iso_code_digit,
            #     'document_type': 'identityNumber'
            # }
            #
            # print(data)
            #
            # final_response = PaystackHelper.verify_account(data)
            # print(final_response)
            #
            # if final_response.status_code != 200:
            #     data = {
            #         'account_name': bank_verified['account_name'],
            #         'account_number': account_number,
            #         'account_type': account_type,
            #         'bank_code': bank_code,
            #         'country_code': iso_code_digit,
            #         'document_type': 'passportNumber'
            #     }
            #
            #     final_response_2 = PaystackHelper.verify_account(data)
            #
            #     if final_response_2.status_code != 200:
            #         print('final fail')
            #         return jsonify({
            #             'code': 400,
            #             'status_message': 'bad request',
            #             'message': 'bank addition failed'
            #         }), 400

            # @TODO: Know your customer
            decrypted_bvn = Cryptographer.decrypt(existing_kyc.bvn)
            encrypted_bvn = Cryptographer.encrypt(decrypted_bvn)

            # noinspection PyArgumentList
            new_bank_detail = BankAccountModel(
                user_id=user_id,
                bvn=encrypted_bvn,
                country=country_name,
                country_code=iso_code_digit,
                bank_name=bank_name,
                bank_code=bank_code,
                account_name=bank_verified['account_name'],
                account_number=account_number,
                account_type=account_type,
                currency=currency,
                # document_type=document_type
            )

            new_bank_detail.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'bank account was successfully added'
            }), 201
        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'this currency has already been listed'
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
        """ Retrieve all currencies """

        bank_accounts = BankAccountModel.query.all()

        try:
            if not bank_accounts:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no account was found'
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
        """ Retrieve a bank account by id """

        bank_accounts = BankAccountModel.query.filter_by(id=id).first()

        try:
            if not bank_accounts:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no account was found'
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
                    'status_message': 'data not found',
                    'message': 'no bank account was found'
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
    def delete(id=None):
        """ Retrieve and delete a currency by id """

        bank_accounts = BankAccountModel.query.filter_by(id=id).first()

        try:
            if not bank_accounts:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no user account was found'
                }), 404

            bank_accounts.delete()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'account was deleted successfully'
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
