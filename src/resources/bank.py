"""
src/resources/bank.py
Exposes bank listing and account resolution, backed by BellBank.

These endpoints feed the local (NGN) transfer flow, and local transfers settle
over BellBank -- the payout hands the selected code to BellBank as
beneficiaryBankCode. They used to be backed by Flutterwave, so the app listed
banks and confirmed the account holder's name against one switch while the
money left through another: a bank code only means something to the provider
that issued it, and a name Flutterwave confirms says nothing about where
BellBank will actually send the funds.

Flutterwave's own bank list is still exposed, unchanged, at /list-banks.
"""

from hmac import compare_digest

from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument

from ..middlewares import BellbankHelper
from ..utilities import parse_params

# BellBank is a Nigerian microfinance bank: its bank list and name enquiry
# cover NGN only, so there is no honest answer for any other country here.
SUPPORTED_COUNTRIES = ('ng', 'nga', 'nigeria')

# Short-lived: the token is used immediately and never stored.
TOKEN_VALIDITY_MINUTES = '5'


class BankResource(Resource):
    """  """

    @staticmethod
    def list_banks(country=None):
        """ Returns the banks reachable for a given country (e.g. 'NG') """

        try:
            if str(country or '').lower() not in SUPPORTED_COUNTRIES:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'only nigerian banks are supported'
                }), 400

            response = BellbankHelper.list_bell_ngn_banks()

            # The helper returns None when it cannot reach the bank rather
            # than a response object, so a status_code check alone would raise.
            if response is None:
                return jsonify({
                    'code': 502,
                    'status_message': 'bad gateway',
                    'message': 'could not reach the bank to fetch the bank list'
                }), 502

            if not compare_digest(str(response.status_code), '200'):
                return jsonify({
                    'code': response.status_code,
                    'status_message': 'failed',
                    'message': 'could not retrieve bank list'
                }), response.status_code

            banks = response.json().get('data', []) or []

            # Normalised here rather than passed through raw: BellBank answers
            # in camelCase, the rest of this API is snake_case, and the client
            # should not have to know which provider replied.
            data = [
                {
                    'bank_code': bank.get('bankCode') or bank.get('code'),
                    'bank_name': bank.get('bankName') or bank.get('name'),
                }
                for bank in banks
            ]

            # A bank we cannot address is not selectable: choosing it would
            # fail at payout with an opaque error long after the user sent.
            data = [b for b in data if b['bank_code'] and b['bank_name']]
            data.sort(key=lambda b: b['bank_name'].lower())

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
        """ Resolves an account number + bank code to the account holder's name """

        try:
            access_token = BellbankHelper.bellbank_authentication(
                TOKEN_VALIDITY_MINUTES)

            if not access_token:
                return jsonify({
                    'code': 502,
                    'status_message': 'bad gateway',
                    'message': 'could not authenticate with the bank'
                }), 502

            # BellBank wants the account number as a number, so whatever the
            # keypad or a paste added has to come off first.
            digits = ''.join(c for c in str(account_number) if c.isdigit())

            if not digits:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'account number must be digits'
                }), 400

            response = BellbankHelper.bell_resolve_account_number(
                int(digits), bank_code, access_token)

            if response is None:
                return jsonify({
                    'code': 502,
                    'status_message': 'bad gateway',
                    'message': 'could not reach the bank to resolve that account'
                }), 502

            if not compare_digest(str(response.status_code), '200'):
                return jsonify({
                    'code': response.status_code,
                    'status_message': 'failed',
                    'message': 'could not resolve account, check the account number and bank'
                }), response.status_code

            resolved = response.json().get('data', {}) or {}
            account_name = resolved.get('accountName')

            # No name means the account was never actually confirmed. Returning
            # 200 with a blank name let the review screen show an empty payee
            # and still offer to send.
            if not account_name:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'that account could not be confirmed'
                }), 404

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': {
                    'account_number': digits,
                    'account_name': account_name,
                }
            }), 200

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500
