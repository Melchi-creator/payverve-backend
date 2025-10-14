"""
app/infrastructure/utilities/paystack_helper.py
this module contains helper methods for making requests to the paystack api
"""

import requests
from flask import jsonify

import config


class PaystackHelper:
    """ this class contains helper methods for making requests to the paystack api """

    @staticmethod
    def paystack_payment(endpoint: str, method: str, data):
        """ this method makes a payment request to the paystack api """

        try:

            url = f'{config.paystack_base_url}/{endpoint}'

            headers = {
                'content-type': 'application/json',
                'authorization': f'Bearer {config.paystack_secret_key}'
            }

            response = requests.request(method, url, headers=headers, json=data)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def verify_payment(reference: str):
        """ this method verifies a payment transaction """

        try:

            url = f'{config.paystack_base_url}/transaction/verify/{reference}'

            headers = {
                'content-type': 'application/json',
                'authorization': f'Bearer {config.paystack_secret_key}'
            }

            response = requests.request('GET', url, headers=headers)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def paystack_bank(endpoint: str, method: str):
        """ this method verifies a payment transaction """

        try:

            url = f'{config.paystack_base_url}/{endpoint}'

            headers = {
                'authorization': f'Bearer {config.paystack_secret_key}'
            }

            response = requests.request(method, url, headers=headers)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def verify_bank(account_number: int, bank_code: int):
        """ this method verifies a payment transaction """

        try:

            url = f'{config.paystack_base_url}/bank/resolve?account_number={account_number}&bank_code={bank_code}'

            headers = {
                'authorization': f'Bearer {config.paystack_secret_key}'
            }

            response = requests.request('GET', url, headers=headers)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def verify_account(data):
        """ this method verifies a payment transaction """

        try:

            url = f'{config.paystack_base_url}/bank/validate'

            headers = {
                'content-type': 'application/json',
                'authorization': f'Bearer {config.paystack_secret_key}'
            }

            print(url)

            response = requests.request('POST', url, headers=headers, json=data)
            print(response)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500
