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
    def flutterwave_ngn_funding():
        """ """

        try:

            account_bank = request.json.get('account_bank')
            account_number = request.json.get('account_number')
            amount = request.json.get('amount')
            currency = request.json.get('currency')
            reference = request.json.get('reference')
            callback_url = request.json.get('callback_url')
            narration = request.json.get('narration')

            url = f'{config.flutterwave_base_url}/transfers'

            headers = {
                'content-type': 'application/json',
                'Authorization': f'Bearer {config.flutterwave_secret_key}',
                'accept': 'application/json'
            }

            payload = {
                "account_bank": account_bank,
                "account_number": account_number,
                "amount": amount,
                "currency": currency.upper(),
                "reference":reference,
                "callback_url": callback_url,
                "narration": narration
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


