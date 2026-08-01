"""
src/resources/bank.py
Exposes bank listing and account resolution, backed by Flutterwave.
"""

from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument

from ..middlewares import FlutterwaveHelper
from ..utilities import parse_params
from hmac import compare_digest


class BankResource(Resource):
    """  """

    @staticmethod
    def list_banks(country=None):
        """ Returns the list of banks available for a given country (e.g. 'NG') """

        try:
            response = FlutterwaveHelper.flutterwave_list_of_banks(country)

            if not compare_digest(str(response.status_code), '200'):
                return jsonify({
                    'code': response.status_code,
                    'status_message': 'failed',
                    'message': 'could not retrieve bank list'
                }), response.status_code

            banks = response.json().get('data', [])

            data = [
                {
                    'bank_code': bank.get('code'),
                    'bank_name': bank.get('name'),
                }
                for bank in banks
            ]

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    @parse_params(
        Argument("account_number", location="json", required=True),
        Argument("bank_code", location="json", required=True),
    )
    def resolve_account(account_number: str, bank_code: str):
        """ Resolves an account number + bank code to the real account holder's name """

        try:
            auth = FlutterwaveHelper.flutterwave_authentication()

            response = FlutterwaveHelper.resolve_bank(
                account_number, bank_code, auth)

            if not compare_digest(str(response.status_code), '200'):
                return jsonify({
                    'code': response.status_code,
                    'status_message': 'failed',
                    'message': 'could not resolve account, check the account number and bank'
                }), response.status_code

            resolved = response.json().get('data', {})

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': {
                    'account_number': resolved.get('account_number'),
                    'account_name': resolved.get('account_name'),
                }
            }), 200

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500
