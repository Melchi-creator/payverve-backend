"""

"""

import requests
from flask import jsonify, request

import config


class FltterwaveHelper:
    """  """

    @staticmethod
    def flutterwave_create_vna():
        """ the method creates a virtual naira account (vna) """

        try:

            email_address = request.json.get('email_address')
            mobile_number = request.json.get('mobile_number')
            first_name = request.json.get('first_name')
            last_name = request.json.get('last_name')
            bvn = request.json.get('bvn')

            url = f'{config.flutterwave_base_url}/virtual-account-numbers'

            headers = {
                'content-type': 'application/json',
                'Authorization': f'Bearer {config.flutterwave_secret_key}'
            }

            payload = {
                "email": email_address,
                "tx_ref": f"ngn-{email_address}",
                "phonenumber": mobile_number,
                "is_permanent": True,
                "firstname": first_name,
                "lastname": last_name,
                "narration": f"{email_address} virtual naira account",
                "bvn": bvn
            }

            response = requests.request('POST', url, headers=headers, json=payload)

            return jsonify({
                'code': response.status_code,
                'code_message': 'success' if response.status_code == 200 else 'failed',
                'data': response.json()
            }), response.status_code

        except Exception as e:
            return jsonify({
                'code': 500,
                'code_message': 'server error',
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
                'code_message': 'server error',
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
                'code_message': 'server error',
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
                'code_message': 'server error',
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
                'code_message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500
