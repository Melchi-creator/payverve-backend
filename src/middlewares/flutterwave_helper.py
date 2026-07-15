"""

"""
import hashlib
import hmac
import secrets

import requests
from flask import jsonify

import config


class FlutterwaveHelper:
    """  """

    @staticmethod
    def flutterwave_authentication():
        """ """

        try:

            url = f'{config.flutterwave_auth_url}/realms/flutterwave/protocol/openid-connect/token'

            data = {
                "client_id": config.flutterwave_client_id,
                "client_secret": config.flutterwave_secret_key,
                "grant_type": "client_credentials"
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.request(
                'POST', url, headers=headers, data=data)
            access_token = response.json().get('access_token')

            return access_token

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def create_flutterwave_account(access_token, email_address, mobile_number, first_name, last_name, middle_name=None):
        """ """

        url = f'{config.flutterwave_base_url}/customers'

        # Flutterwave rejects local-format numbers with a leading 0 (e.g. 08011112222)
        # since country_code is passed separately; strip it before sending.
        normalized_number = mobile_number.lstrip(
            '0') if mobile_number else mobile_number

        message = f'{email_address}{mobile_number}{first_name}{last_name}{middle_name}'
        idempotency_key = hmac.new(config.secret_key.encode(
        ), message.encode(), hashlib.sha256).hexdigest()

        headers = {
            'content-type': 'application/json',
            'accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'X-Trace-Id': secrets.token_urlsafe(12),
            'X-Idempotency-Key': idempotency_key
        }

        payload = {
            "email": email_address,
            "phone": {
                "country_code": "234",
                "number": normalized_number
            },
            "name": {
                "first": first_name,
                "middle": middle_name,
                "last": last_name
            }
        }

        response = requests.request('POST', url, headers=headers, json=payload)
        print("CREATE CUSTOMER STATUS:", response.status_code)
        print("CREATE CUSTOMER BODY:", response.text)

        return response

    @staticmethod
    def search_for_customer(access_token, email_address):
        """ """

        try:

            url = f'{config.flutterwave_base_url}/customers/search'

            message = f'{email_address}'
            idempotency_key = hmac.new(config.secret_key.encode(
            ), message.encode(), hashlib.sha256).hexdigest()

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'X-Trace-Id': secrets.token_urlsafe(12),
                'X-Idempotency-Key': idempotency_key
            }

            payload = {
                "email": email_address,
            }

            response = requests.request(
                'POST', url, headers=headers, json=payload)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def virtual_account(access_token, reference_number, customer_id, email_address, short_code, user_datails, kyc_check):
        """ """

        try:

            url = f'{config.flutterwave_base_url}/virtual-accounts'

            message = f'{email_address}{0}{short_code.upper()}'
            idempotency_key = hmac.new(config.secret_key.encode(
            ), message.encode(), hashlib.sha256).hexdigest()

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'X-Trace-Id': secrets.token_urlsafe(12),
                'X-Idempotency-Key': idempotency_key
            }

            full_name = f"{user_datails.first_name} {user_datails.last_name}"

            payload = {
                "reference": reference_number,
                "customer_id": customer_id,
                "amount": 0,
                "currency": short_code.upper(),
                "account_type": "static",
                "narration": f"Payverve/{full_name}",
            }

            if short_code.lower() == 'ngn':
                payload['bank_code'] = '090772'
                payload['bvn'] = kyc_check.bvn

            if short_code.lower() == 'ghs':
                payload['bank_code'] = 'GH200100'

            print(payload)

            response_va = requests.request(
                'POST', url, headers=headers, json=payload)

            print(response_va.text)

            return response_va

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def retreive_virtual_account(access_token, virtual_account_id):
        """ """

        try:

            url = f'{config.flutterwave_base_url}/virtual-accounts/{virtual_account_id}'

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'X-Trace-Id': secrets.token_urlsafe(12),
            }

            response = requests.request('GET', url, headers=headers)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def flutterwave_list_of_banks(country):
        """ """

        try:

            url = f'{config.flutterwave_base_url}/banks/{country}?include_provider_type=1'

            access_token = FlutterwaveHelper.flutterwave_authentication()

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'X-Idempotency-Key': secrets.token_urlsafe(12),
                'X-Trace-Id': secrets.token_urlsafe(12)
            }

            response = requests.request('GET', url, headers=headers)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def resolve_bank(account_number, bank_code, access_token):
        """ """

        try:

            url = f'{config.flutterwave_base_url}/accounts/resolve'

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }

            payload = {
                "account_number": int(account_number),
                "account_bank": int(bank_code)
            }

            response = requests.request(
                'POST', url, headers=headers, json=payload)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500
