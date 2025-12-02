"""

"""
import hashlib
import hmac
import json
import secrets

import requests
from flask import jsonify, request
from psycopg2 import DataError, InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DBAPIError, DisconnectionError

import config


class BellbankHelper:
    """  """

    @staticmethod
    def bellbank_authentication(minutes):
        """ """

        try:

            url = f'{config.bellbank_baseurl}/generate-token'

            headers = {
                "Content-Type": "application/json",
                "consumerKey": config.bellbank_consumer_key,
                "consumerSecret": config.bellbank_consumer_secret,
                "validityTime": minutes
            }

            response = requests.request('POST', url, headers=headers)
            access_token = response.json().get('token')

            return access_token

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def bellbank_virtual_account(access_token, mobile_number, first_name, last_name, address, bvn, gender,
                                 date_of_birth, meta_data=None, middle_name=None):
        """ """

        try:

            url = f'{config.bellbank_baseurl}/account/clients/individual'

            message = f'{gender}{mobile_number}{first_name}{last_name}'
            idempotency_key = hmac.new(config.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'X-Trace-Id': secrets.token_urlsafe(12),
                'X-Idempotency-Key': idempotency_key
            }

            payload = {
                "firstname": first_name,
                "lastname": last_name,
                "middlename": middle_name,
                "phoneNumber": mobile_number,
                "address": address,
                "bvn": bvn,
                "gender": gender,
                "dateOfBirth": date_of_birth,
                "metadata": meta_data,
            }

            response = requests.request('POST', url, headers=headers, json=payload)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def list_bell_ngn_banks():
        """ """

        try:

            url = f'{config.bellbank_baseurl}/transfer/banks'
            access_token = BellbankHelper.bellbank_authentication('2')

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
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
    def bell_resolve_account_number(account: int, bank_code: str, access_token):
        """ """

        try:

            url = f'{config.bellbank_baseurl}/transfer/name-enquiry'

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }

            payload = {
                "accountNumber": account,
                "bankCode": bank_code
            }

            response = requests.request('POST', url, headers=headers, json=payload)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def transfer_outbound(bank_code, amount, narration, account_number, reference, sender_name, recipient_name,
                          access_token):
        """ """

        try:

            url = f'{config.bellbank_baseurl}/transfer'

            message = f'{sender_name}{amount}{bank_code}{account_number}{recipient_name}'
            idempotency_key = hmac.new(config.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'X-Trace-Id': secrets.token_urlsafe(12),
                'X-Idempotency-Key': idempotency_key
            }

            payload = {
                "beneficiaryBankCode": bank_code,
                "beneficiaryAccountNumber": account_number,
                "narration": narration,
                "amount": amount,
                "reference": reference,
                "senderName": sender_name,
            }

            response = requests.request('POST', url, headers=headers, json=payload)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def bellbank_webhook():
        """  """

        try:

            # Get the request body as raw data
            payload = request.data

            # Parse the payload
            webhook_data = json.loads(payload)

            event = webhook_data.get('collection')

            print(event)

            return jsonify({
                'code': 200,
                'code_message': 'success',
                'data': 'Webhook received successfully'
            }), 200

        except json.JSONDecodeError:
            return jsonify({
                'code': 400,
                'code_message': 'bad request',
                'data': 'Invalid JSON payload'
            }), 400

        except DataError:
            return jsonify({
                "code": 400,
                'code_message': 'bad request',
                "data": "Invalid data format",
            }), 400

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'code_message': 'database error',
                "data": "A database error occurred",
            }), 500

        except Exception as e:
            return jsonify({
                "code": 500,
                'code_message': 'server error',
                "data": f"An unexpected error occurred {str(e)}",
            }), 500
    #
    # @staticmethod
    # def buy_property_status(event, data, reference):
    #     """ """
    #
    #     try:
    #
    #         buy_property_transaction = InitiateBuyModel.query.filter_by(reference=reference).first()
    #
    #         if buy_property_transaction:
    #             if buy_property_transaction.status == 'pending':
    #                 status = data.get('status')
    #
    #                 if event == 'charge.success' and status == 'success':
    #                     BuyPropertyService.confirm_payment(reference)
    #
    #                     return True
    #
    #         return False
    #
    #     except DataError:
    #         return jsonify({
    #             "code": 400,
    #             'code_message': 'bad request',
    #             "data": f"Invalid data format",
    #         }), 400
    #
    #     except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
    #         return jsonify({
    #             "code": 500,
    #             'code_message': 'database error',
    #             "data": "A database error occurred",
    #         }), 500
