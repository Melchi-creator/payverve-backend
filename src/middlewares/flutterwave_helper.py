"""

"""
import hashlib
import hmac
import secrets

import requests
from flask import jsonify, request

import config
import base64
import json
from hmac import compare_digest

from psycopg2 import DataError, InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DBAPIError, DisconnectionError
from ..models import UserModel

from ..models import TransactionModel, VirtualAccountNumberModel, WalletModel
from ..resources.notification import NotificationResource
from ..utilities import Cryptographer
from ..utilities.push_notifications import send_push_notification


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

    @staticmethod
    def flutterwave_webhook():
        """ Handle Flutterwave charge.completed webhooks for virtual account (bank transfer) deposits """

        try:
            raw_body = request.get_data()

            signature = request.headers.get('flutterwave-signature')
            expected_signature = base64.b64encode(
                hmac.new(
                    config.flutterwave_secret_hash.encode(),
                    raw_body,
                    hashlib.sha256
                ).digest()
            ).decode()

            if not signature or not compare_digest(signature, expected_signature):
                return jsonify({
                    'code': 401,
                    'status_message': 'unauthorized',
                    'message': 'invalid webhook signature'
                }), 401

            payload = json.loads(raw_body)

            if not compare_digest(str(payload.get('type')), 'charge.completed'):
                return 'event ignored', 200

            data = payload.get('data') or {}

            payment_method_details = data.get(
                'payment_method_details') or data.get('payment_method') or {}
            payment_type = payment_method_details.get('type')

            if not compare_digest(str(payment_type), 'bank_transfer'):
                return 'event ignored', 200

            if not compare_digest(str(data.get('status')), 'succeeded'):
                return 'event ignored', 200

            charge_id = data.get('id')

            if not charge_id:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'missing charge id'
                }), 400

            # Idempotency: bail out if we've already processed this charge
            existing = TransactionModel.query.filter_by(
                flw_ref=charge_id).first()
            if existing:
                return 'already processed', 200

            customer = data.get('customer') or {}
            customer_id = customer.get('id')

            if not customer_id:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'missing customer id'
                }), 400

            virtual_account = VirtualAccountNumberModel.query.filter_by(
                customer_code=customer_id).first()

            if not virtual_account:
                # We received a valid, verified deposit event but can't match it to a known
                # virtual account. Acknowledge receipt so Flutterwave doesn't retry, but this
                # needs manual investigation.
                return jsonify({
                    'code': 200,
                    'status_message': 'unmatched',
                    'message': 'no matching virtual account for this customer'
                }), 200

            wallet = WalletModel.query.filter_by(
                user_id=virtual_account.user_id,
                currency_id=virtual_account.currency_id
            ).first()

            if not wallet:
                return jsonify({
                    'code': 200,
                    'status_message': 'unmatched',
                    'message': 'no matching wallet for this virtual account'
                }), 200
            # auth = FlutterwaveHelper.flutterwave_authentication()
            # verify_response = FlutterwaveHelper.retrieve_charge(
            #     auth, charge_id)

            # if not compare_digest(str(verify_response.status_code), '200'):
            #     return jsonify({
            #         'code': 200,
            #         'status_message': 'verification failed',
            #         'message': 'could not verify charge with Flutterwave, will not credit wallet'
            #     }), 200
            # verified_charge = verify_response.json().get('data') or {}
            # verified_payment_method = verified_charge.get(
            #     'payment_method_details') or verified_charge.get('payment_method') or {}

            # if not compare_digest(str(verified_charge.get('status')), 'succeeded'):
            #     return jsonify({
            #         'code': 200,
            #         'status_message': 'unverified',
            #         'message': 'charge status did not verify as succeeded'
            #     }), 200

            # if not compare_digest(str(verified_payment_method.get('type')), 'bank_transfer'):
            #     return jsonify({
            #         'code': 200,
            #         'status_message': 'unverified',
            #         'message': 'payment method did not verify as bank_transfer'
            #     }), 200

            # verified_customer_id = verified_charge.get('customer_id')

            # if not compare_digest(str(verified_customer_id), str(customer_id)):
            #     return jsonify({
            #         'code': 200,
            #         'status_message': 'unverified',
            #         'message': 'customer id mismatch between webhook and verified charge'
            #     }), 200

            # # Use the verified amount/currency, not the webhook's — this is the whole point of re-querying
            # amount_received = verified_charge.get('amount')
            # currency = verified_charge.get('currency')
            # reference = verified_charge.get('reference')
            if config.skip_flw_verification_for_testing:
                # LOCAL TESTING ONLY — bypasses real Flutterwave charge verification.
                # Must never be enabled outside a local .env file.
                print("WARNING: Skipping Flutterwave charge verification (test mode).")
                amount_received = data.get('amount')
                currency = data.get('currency')
                reference = data.get('reference')
                verified_payment_method = payment_method_details
            else:
                auth = FlutterwaveHelper.flutterwave_authentication()
                verify_response = FlutterwaveHelper.retrieve_charge(
                    auth, charge_id)

                if not compare_digest(str(verify_response.status_code), '200'):
                    return jsonify({
                        'code': 200,
                        'status_message': 'verification failed',
                        'message': 'could not verify charge with Flutterwave, will not credit wallet'
                    }), 200
                verified_charge = verify_response.json().get('data') or {}
                verified_payment_method = verified_charge.get(
                    'payment_method_details') or verified_charge.get('payment_method') or {}

                if not compare_digest(str(verified_charge.get('status')), 'succeeded'):
                    return jsonify({
                        'code': 200,
                        'status_message': 'unverified',
                        'message': 'charge status did not verify as succeeded'
                    }), 200

                if not compare_digest(str(verified_payment_method.get('type')), 'bank_transfer'):
                    return jsonify({
                        'code': 200,
                        'status_message': 'unverified',
                        'message': 'payment method did not verify as bank_transfer'
                    }), 200

                verified_customer_id = verified_charge.get('customer_id')

                if not compare_digest(str(verified_customer_id), str(customer_id)):
                    return jsonify({
                        'code': 200,
                        'status_message': 'unverified',
                        'message': 'customer id mismatch between webhook and verified charge'
                    }), 200

                # Use the verified amount/currency, not the webhook's — this is the whole point of re-querying
                amount_received = verified_charge.get('amount')
                currency = verified_charge.get('currency')
                reference = verified_charge.get('reference')

            if not compare_digest(str(currency), str(virtual_account.currency_ticker)):
                return jsonify({
                    'code': 200,
                    'status_message': 'unverified',
                    'message': 'currency mismatch between verified charge and virtual account'
                }), 200

            balance = Cryptographer.decrypt(wallet.fund)
            new_balance = float(balance) + float(amount_received)
            wallet.fund = Cryptographer.encrypt(str(new_balance))
            wallet.save()

            originator_name = verified_payment_method.get(
                'bank_transfer', {}).get('originator_name')

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=Cryptographer.encrypt(amount_received),
                transaction_type='flutterwave_deposit',
                tx_ref=reference,
                flw_ref=charge_id,
                user_id=wallet.user_id,
                currency_id=wallet.currency_id,
                note='Wallet funded via bank transfer',
                status='successful',
                transaction_flow='credit',
                transaction_title='Money Received',
                name=originator_name or 'Bank Transfer',
                currency_ticker=currency.lower() if currency else wallet.currency_ticker,
            )
            new_transaction.save()

            NotificationResource.store_nofication(
                title="Wallet Funded",
                body=f"Your wallet was credited with {currency} {float(amount_received):,.2f}",
                user_id=wallet.user_id,
            )

            user = UserModel.query.filter_by(id=wallet.user_id).first()
            if user and user.fcm_token:
                send_push_notification(
                    fcm_token=user.fcm_token,
                    title="Wallet Funded",
                    body=f"Your wallet was credited with {currency} {float(amount_received):,.2f}",
                    data={"type": "wallet_credit",
                          "amount": str(amount_received)},
                )

            return 'webhook processed', 200

        except json.JSONDecodeError:
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'invalid JSON payload'
            }), 400

        except (DataError, ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'a database error occurred'
            }), 500

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an unexpected error occurred: {str(e)}'
            }), 500

    @staticmethod
    def retrieve_charge(access_token, charge_id):
        """ Retrieve the authoritative charge details from Flutterwave before crediting a wallet """

        try:
            url = f'{config.flutterwave_base_url}/charges/{charge_id}'

            headers = {
                'content-type': 'application/json',
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }

            response = requests.request('GET', url, headers=headers)
            print("RETRIEVE CHARGE STATUS:", response.status_code)
            print("RETRIEVE CHARGE BODY:", response.text)

            return response

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500
