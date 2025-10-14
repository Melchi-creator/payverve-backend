"""

"""

import requests
from flask import jsonify, request

import config
from src.models import CurrencyModel, WalletModel
from src.models.transaction import TransactionModel
from src.utilities import Cryptographer


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
                'message': 'success' if response.status_code == 200 else 'failed',
                'data': response.json()
            }), response.status_code

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
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
                "reference": reference,
                "callback_url": callback_url,
                "narration": narration
            }

            response = requests.request('POST', url, headers=headers, json=payload)

            return jsonify({
                'code': response.status_code,
                'message': 'success' if response.status_code == 200 else 'failed',
                'data': response.json()
            }), response.status_code

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def flutterwave_list_of_banks():
        """ """

        try:

            country = request.json.get('country').upper()

            url = f'{config.flutterwave_base_url}/banks/{country}?include_provider_type=1'

            headers = {
                'content-type': 'application/json',
                'Authorization': f'Bearer {config.flutterwave_secret_key}'
            }

            response = requests.request('GET', url, headers=headers)

            return jsonify({
                'code': response.status_code,
                'message': 'success' if response.status_code == 200 else 'failed',
                'data': response.json()
            }), response.status_code

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            }), 500

    @staticmethod
    def flutterwave_webhook():
        """ """

        try:

            secret_hash = config.flutterwave_secret_hash
            signature = request.headers.get("verifi-hash")
            if signature is None or (signature != secret_hash):
                return jsonify({
                    'code': 401,
                    'message': 'signature verification failed',
                    'data': 'signature verification failed'
                }), 401

            data = request.get_json()

            # Make sure payload is valid
            if not data or "event" not in data:
                return jsonify({
                    'code': 400,
                    'message': 'invalid request',
                    'data': 'invalid request'
                }), 400

            event = data.get("event")
            event_type = event.get("event.type")
            tx_data = data.get("data", {})

            # Only handle successful charges
            if event == "charge.completed" and tx_data.get("status") == "successful":
                tx_ref = tx_data.get("tx_ref")
                flw_ref = tx_data.get("flw_ref")
                amount = tx_data.get("amount")
                customer_email = tx_data.get("customer", {}).get("email")
                currency = tx_data.get("currency")

                from src.models import UserModel
                user_id = UserModel.query.filter_by(email_address=customer_email).first().id
                transaction = TransactionModel.query.filter_by(user_id=user_id, flw_ref=flw_ref).first()

                transaction_type = None

                if event_type == "BANK_TRANSFER_TRANSACTION":
                    transaction_type = "wallet_funding"

                encrypt_amount = Cryptographer.encrypt(amount)

                if not transaction:
                    currency_id = CurrencyModel.query.filter_by(short_code=currency.lower()).first().id

                    # noinspection PyArgumentList
                    new_transaction = TransactionModel(
                        tx_ref=tx_ref,
                        flw_ref=flw_ref,
                        amount=encrypt_amount,
                        transaction_type=transaction_type,
                        user_id=user_id,
                        currency_id=currency_id,
                        note='bank transfer'
                    )

                    user_wallet = WalletModel.query.filter_by(user_id=user_id, currency_ticker=currency.lower()).first()
                    decrypt_balance = Cryptographer.decrypt(user_wallet.fund)

                    new_balance = float(decrypt_balance) + float(amount)
                    encrypt_balance = Cryptographer.encrypt(new_balance)
                    user_wallet.fund = encrypt_balance
                    user_wallet.save()

                    new_transaction.save()

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': 'transaction successful'
            }), 200

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': 'server error',
                'data': f'an error occurred: {str(e)}'
            })
