"""

"""
import hashlib
import hmac
import json
import secrets
from hmac import compare_digest

import requests
from flask import jsonify, request
from psycopg2 import DataError, InternalError, OperationalError, ProgrammingError
from sqlalchemy.exc import DBAPIError, DisconnectionError

import config
from ..models import (InboundTransferModel, TransactionModel,
                      VirtualAccountNumberModel, WalletModel)
from src.resources.notification import NotificationResource
from ..utilities import Cryptographer


BELLBANK_API_VERSION = 'v1'


def bellbank_url(path):
    """Build a BellBank endpoint URL.

    Every call used to be built as f'{bellbank_baseurl}{path}', and
    BELLBANK_BASEURL is the bare host, so all of them hit nginx and came back
    404: the documented paths are /v1/generate-token,
    /v1/account/clients/individual and so on. Tolerates a base url that already
    carries the prefix, so setting it either way works.
    """
    base = (config.bellbank_baseurl or '').rstrip('/')

    if not base.endswith('/' + BELLBANK_API_VERSION):
        base = f'{base}/{BELLBANK_API_VERSION}'

    return f"{base}/{path.lstrip('/')}"


class BellbankHelper:
    """  """

    @staticmethod
    def bellbank_authentication(minutes):
        """ """

        try:

            url = bellbank_url('generate-token')

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

            url = bellbank_url('account/clients/individual')

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

            url = bellbank_url('transfer/banks')
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

            url = bellbank_url('transfer/name-enquiry')

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

            url = bellbank_url('transfer')

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
    def transfer_requery(reference, access_token):
        """ """

        try:

            url = bellbank_url(f'transactions/reference/{reference}')

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
    def verify_bellbank_signature(raw_payload):
        """
        Confirm the request really came from BellBank.

        This endpoint credits customer wallets, so it cannot be authenticated
        with jwt_required -- BellBank has no Payverve JWT to send, which is why
        every collection notification was being rejected with 401. It is
        authenticated with the shared secret instead.

        Fails closed: an unset secret, a missing header or a mismatch are all
        rejected. Without this, anyone who learns the URL could POST a forged
        'collection' event and credit any account number.
        """
        secret = getattr(config, 'bellbank_webhook_secret', None)

        if not secret:
            print('[bellbank] BELLBANK_WEBHOOK_SECRET is not set; '
                  'rejecting webhook. Deposits cannot be credited until it is '
                  'configured.')
            return False

        header_name = getattr(
            config, 'bellbank_webhook_signature_header', 'X-Signature')
        sent_signature = request.headers.get(header_name)

        if not sent_signature:
            print(f'[bellbank] webhook rejected: no {header_name} header')
            return False

        expected = hmac.new(
            secret.encode(), raw_payload, hashlib.sha256
        ).hexdigest()

        # compare_digest avoids leaking the signature through timing.
        if not hmac.compare_digest(expected, sent_signature.strip()):
            print('[bellbank] webhook rejected: signature mismatch')
            return False

        return True

    @staticmethod
    def virtual_account_for_wallet(wallet):
        """The BellBank account number a wallet receives into, or None."""
        if wallet is None:
            return None

        virtual_account = VirtualAccountNumberModel.query.filter_by(
            user_id=wallet.user_id, currency_id=wallet.currency_id).first()

        return virtual_account.account_number if virtual_account else None

    @staticmethod
    def wallet_for_virtual_account(account_number):
        """Find the NGN wallet that owns a BellBank virtual account.

        The account number lives on virtual_account_numbers; wallets lost that
        column in migration 2129b3c36f79. Stored as a string there, while the
        webhook may send it as either, so both are tried.
        """
        if account_number in (None, ''):
            return None

        virtual_account = VirtualAccountNumberModel.query.filter_by(
            account_number=str(account_number)).first()

        if not virtual_account:
            return None

        return WalletModel.query.filter_by(
            user_id=virtual_account.user_id,
            currency_id=virtual_account.currency_id).first()

    @staticmethod
    def bellbank_webhook():
        """  """

        try:

            # Get the request body as raw data
            payload = request.data

            # Verify before parsing or touching any balance.
            if not BellbankHelper.verify_bellbank_signature(payload):
                return jsonify({
                    'code': 401,
                    'code_message': 'unauthorised',
                    'data': 'invalid webhook signature'
                }), 401

            # Parse the payload
            webhook_data = json.loads(payload)

            event = webhook_data.get('event')

            if compare_digest(str(event), 'collection'):

                source_account_number = webhook_data.get('sourceAccountNumber')
                recipient_account_number = webhook_data.get('virtualAccount')
                transaction_status = webhook_data.get('status')

                if compare_digest(str(transaction_status), 'successful'):

                    # The wallet to CREDIT is the one that owns the virtual
                    # account the money landed in. Both handlers below expect a
                    # wallet object -- they were being passed the recipient
                    # account number as a string, so every credit raised
                    # AttributeError and returned 500.
                    #
                    # Account details live on virtual_account_numbers, not on
                    # the wallet: migration 2129b3c36f79 dropped
                    # wallets.account_number, so filtering wallets on it raised
                    # InvalidRequestError on every notification.
                    recipient_wallet = BellbankHelper.wallet_for_virtual_account(
                        recipient_account_number)

                    if not recipient_wallet:
                        print('[bellbank] no wallet for virtual account '
                              f'{recipient_account_number}; ignoring')
                        return 'webhook received', 200

                    # The sender lookup only classifies the transfer as
                    # internal (Payverve to Payverve) or external.
                    sender_wallet = BellbankHelper.wallet_for_virtual_account(
                        source_account_number)

                    if sender_wallet:
                        BellbankHelper.payverve_to_payverve_transfer(
                            webhook_data, recipient_wallet)

                    if not sender_wallet:
                        BellbankHelper.others_to_payverve_transfer(
                            webhook_data, recipient_wallet)

            return 'webhook received', 200

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

    @staticmethod
    def payverve_to_payverve_transfer(data, payverve_wallet):
        """  """

        try:

            recipient_account_number = data.get('virtualAccount')

            # Resolved through virtual_account_numbers; the wallet no longer
            # carries the account number.
            wallet_account_number = BellbankHelper.virtual_account_for_wallet(
                payverve_wallet)

            if not compare_digest(str(recipient_account_number), str(wallet_account_number)):
                return jsonify({
                    "code": 400,
                    'code_message': 'bad request',
                    "data": "Recipient account number does not match Payverve wallet account number",
                }), 400

            amount_received = data.get('amountReceived')
            charge_amount = data.get('transactionFee')
            sender_name = data.get('sourceAccountName')
            sender_account_number = data.get('sourceAccountNumber')
            sender_bank = data.get('sourceBankName')
            narration = data.get('remarks')
            reference_number = data.get('externalReference')
            session_id = data.get('sessionId')
            stamp_duty = data.get('stampDuty')

            # Idempotency. Providers retry webhooks on timeout or a non-2xx,
            # so the same sessionId can arrive more than once. This previously
            # detected the duplicate and then renamed it
            # (f"{session_id}-unique-...") so it was no longer a duplicate --
            # and credited the wallet a second time. Stop instead.
            find_session = InboundTransferModel.query.filter_by(
                session_id=session_id).first()

            if find_session:
                print(f'[bellbank] duplicate webhook for session {session_id}; '
                      'already credited, ignoring')
                return jsonify({
                    'code': 200,
                    'code_message': 'ok',
                    'data': 'transaction already processed'
                }), 200

            balance = Cryptographer.decrypt(payverve_wallet.fund)
            new_balance = float(balance) + float(amount_received)
            payverve_wallet.fund = Cryptographer.encrypt(str(new_balance))
            payverve_wallet.save()

            encrypted_amount = Cryptographer.encrypt(amount_received)

            # noinspection PyArgumentList
            new_local_transfer = InboundTransferModel(
                amount=encrypted_amount,
                charge_amount=charge_amount,
                sender_name=sender_name,
                sender_account_number=sender_account_number,
                narration=narration,
                recipient_name=f'{payverve_wallet.user.first_name} {payverve_wallet.user.last_name}',
                recipient_bank="Payverve Bank",
                recipient_account_number=f'{wallet_account_number}',
                reference_number=reference_number,
                session_id=session_id,
                stamp_duty=stamp_duty,
                sender_bank=sender_bank,
                user_id=payverve_wallet.user_id,
                wallet_id=payverve_wallet.id,
                transaction_status="successful",
            )
            new_local_transfer.save()

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=encrypted_amount,
                transaction_type='payverve_transfer',
                user_id=payverve_wallet.user_id,
                currency_id=payverve_wallet.currency_id,
                note=narration,
                status="successful",
                name=f'{payverve_wallet.user.first_name} {payverve_wallet.user.last_name}',
                transaction_flow='credit',
                transaction_title='Money Received',
                currency_ticker='ngn'
            )

            new_transaction.save()

            NotificationResource.store_nofication(
                title="Payverve Transfer",
                body=f"{payverve_wallet.currency_ticker}{float(amount_received): ,.2f} was received from {sender_name} | {sender_account_number}",
                user_id=payverve_wallet.user_id,
            )

            # Debit Charges

            balance = Cryptographer.decrypt(payverve_wallet.fund)
            new_balance = float(balance) - float(charge_amount)
            payverve_wallet.fund = Cryptographer.encrypt(str(new_balance))
            payverve_wallet.save()

            encrypted_amount = Cryptographer.encrypt(charge_amount)

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=encrypted_amount,
                transaction_type='transaction_charges',
                user_id=payverve_wallet.user_id,
                currency_id=payverve_wallet.currency_id,
                note=f"₦{float(charge_amount): ,.2f} charged for inbound transfer on ₦{float(amount_received): ,.2f} received from {sender_name} | {sender_account_number}",
                status="successful",
                name=f'{payverve_wallet.user.first_name} {payverve_wallet.user.last_name}',
                transaction_flow='debit',
                transaction_title='Bank Charge',
                currency_ticker='ngn'
            )

            new_transaction.save()

            NotificationResource.store_nofication(
                title="Bank Charge",
                body=f"₦{float(charge_amount): ,.2f}  bank charge for inbound transfer on ₦{float(amount_received): ,.2f} received from {sender_name} | {sender_account_number}",
                user_id=payverve_wallet.user_id,
            )

            return 'transfer recorded', 201

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

    @staticmethod
    def others_to_payverve_transfer(data, payverve_wallet):
        """  """

        try:

            recipient_account_number = data.get('virtualAccount')

            # Resolved through virtual_account_numbers; the wallet no longer
            # carries the account number.
            wallet_account_number = BellbankHelper.virtual_account_for_wallet(
                payverve_wallet)

            if not compare_digest(str(recipient_account_number), str(wallet_account_number)):
                return jsonify({
                    "code": 400,
                    'code_message': 'bad request',
                    "data": "Recipient account number does not match Payverve wallet account number",
                }), 400

            amount_received = data.get('amountReceived')
            charge_amount = data.get('transactionFee')
            sender_name = data.get('sourceAccountName')
            sender_account_number = data.get('sourceAccountNumber')
            sender_bank = data.get('sourceBankName')
            narration = data.get('remarks')
            reference_number = data.get('externalReference')
            session_id = data.get('sessionId')
            stamp_duty = data.get('stampDuty')

            # Idempotency. Providers retry webhooks on timeout or a non-2xx,
            # so the same sessionId can arrive more than once. This previously
            # detected the duplicate and then renamed it
            # (f"{session_id}-unique-...") so it was no longer a duplicate --
            # and credited the wallet a second time. Stop instead.
            find_session = InboundTransferModel.query.filter_by(
                session_id=session_id).first()

            if find_session:
                print(f'[bellbank] duplicate webhook for session {session_id}; '
                      'already credited, ignoring')
                return jsonify({
                    'code': 200,
                    'code_message': 'ok',
                    'data': 'transaction already processed'
                }), 200

            balance = Cryptographer.decrypt(payverve_wallet.fund)
            new_balance = float(balance) + float(amount_received)
            payverve_wallet.fund = Cryptographer.encrypt(str(new_balance))
            payverve_wallet.save()

            encrypted_amount = Cryptographer.encrypt(amount_received)

            # noinspection PyArgumentList
            new_local_transfer = InboundTransferModel(
                amount=encrypted_amount,
                charge_amount=charge_amount,
                sender_name=sender_name,
                sender_account_number=sender_account_number,
                narration=narration,
                recipient_name=f'{payverve_wallet.user.first_name} {payverve_wallet.user.last_name}',
                recipient_bank="Payverve Bank",
                recipient_account_number=f'{wallet_account_number}',
                reference_number=reference_number,
                session_id=session_id,
                stamp_duty=stamp_duty,
                sender_bank=sender_bank,
                user_id=payverve_wallet.user_id,
                wallet_id=payverve_wallet.id,
                transaction_status="successful",
            )
            new_local_transfer.save()

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=encrypted_amount,
                transaction_type='local_transfer',
                user_id=payverve_wallet.user_id,
                currency_id=payverve_wallet.currency_id,
                note=narration,
                status="successful",
                name=f'{payverve_wallet.user.first_name} {payverve_wallet.user.last_name}',
                transaction_flow='credit',
                transaction_title='Money Received',
                currency_ticker='ngn'
            )

            new_transaction.save()

            NotificationResource.store_nofication(
                title="Local Transfer",
                body=f"₦{float(amount_received): ,.2f} was received from {sender_name} | {sender_account_number}",
                user_id=payverve_wallet.user_id,
            )

            # Debit Charges

            balance = Cryptographer.decrypt(payverve_wallet.fund)
            new_balance = float(balance) - float(charge_amount)
            payverve_wallet.fund = Cryptographer.encrypt(str(new_balance))
            payverve_wallet.save()

            encrypted_amount = Cryptographer.encrypt(charge_amount)

            # noinspection PyArgumentList
            new_transaction = TransactionModel(
                amount=encrypted_amount,
                transaction_type='transaction_charges',
                user_id=payverve_wallet.user_id,
                currency_id=payverve_wallet.currency_id,
                note=f"₦{float(charge_amount): ,.2f} charged for inbound transfer on ₦{float(amount_received): ,.2f} received from {sender_name} | {sender_account_number}",
                status="successful",
                name=f'{payverve_wallet.user.first_name} {payverve_wallet.user.last_name}',
                transaction_flow='debit',
                transaction_title='Bank Charge',
                currency_ticker='ngn'
            )

            new_transaction.save()

            NotificationResource.store_nofication(
                title="Bank Charge",
                body=f"₦{float(charge_amount): ,.2f}  bank charge for inbound transfer on ₦{float(amount_received): ,.2f} received from {sender_name} | {sender_account_number}",
                user_id=payverve_wallet.user_id,
            )

            return 'transfer recorded', 201

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
