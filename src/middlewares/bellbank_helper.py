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

# No call had a timeout, so a hung connection to BellBank pinned a worker
# indefinitely. Connect and read, in seconds.
BELLBANK_TIMEOUT = (10, 45)


def bellbank_proxies():
    """The proxy BellBank calls go out through, or None to go direct.

    BellBank only answers API calls from whitelisted addresses ('IP Address Not
    Whitlisted' otherwise), and Render's outbound addresses are ranges shared
    with every other Render customer in the region. BELLBANK_PROXY_URL points
    at a static-IP proxy (Fixie, QuotaGuard Static, or our own VPS), so BellBank
    only has to whitelist that proxy's addresses. Only BellBank traffic uses it.

    The URL usually carries the proxy's username and password, so it is never
    logged.
    """
    proxy_url = (getattr(config, 'bellbank_proxy_url', '') or '').strip()

    if not proxy_url:
        return None

    # HTTPS requests are tunnelled through the proxy with CONNECT, so the
    # proxy sees only the host name, never the request or the bank's response.
    return {'http': proxy_url, 'https': proxy_url}


def _keys(value):
    """Sorted keys of a dict, for logging a response's shape without values."""
    return sorted(value.keys()) if isinstance(value, dict) else None


def _client_list(body):
    """The client records in a GET /v1/account/clients response, or None.

    The docs show them as a list under 'data'. Paginated APIs often nest the
    list one level deeper instead, so the usual wrappers are accepted too.
    """
    if not isinstance(body, dict):
        return None

    data = body.get('data')

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ('data', 'items', 'clients', 'docs', 'rows', 'results',
                    'records'):
            if isinstance(data.get(key), list):
                return data[key]

    return None


def bellbank_request(method, url, **kwargs):
    """Every BellBank call goes through here, so each one is bounded by
    BELLBANK_TIMEOUT and leaves through the proxy when one is configured."""
    return requests.request(method, url, timeout=BELLBANK_TIMEOUT,
                            proxies=bellbank_proxies(), **kwargs)


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

            response = bellbank_request('POST', url, headers=headers)

            access_token = response.json().get('token')

            return access_token

        except Exception as e:
            # None rather than a jsonify tuple: callers read .status_code off
            # this, or interpolate it into an Authorization header, so a tuple
            # turned a bank outage into an AttributeError or a request sent as
            # 'Bearer (<Response ...>, 500)'.
            print(f'[bellbank] request failed: {type(e).__name__}: {e}')
            return None

    @staticmethod
    def bellbank_virtual_account(access_token, mobile_number, first_name, last_name, address, bvn, gender,
                                 date_of_birth, meta_data=None, middle_name=None,
                                 email_address=None):
        """Create the customer at BellBank, which issues their account number.

        Field names and formats follow /v1/account/clients/individual in
        BellBank's docs. emailAddress was missing, and BellBank does not
        validate its input: it ran a lookup on the absent field and answered
        500 'WHERE parameter "emailAddress" has invalid "undefined" value'.
        """

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
                "emailAddress": email_address,
                "address": address,
                "bvn": bvn,
                # Documented as 'male' or 'female'.
                "gender": str(gender or '').strip().lower(),
                # Documented as 1993/12/29.
                "dateOfBirth": (date_of_birth.strftime('%Y/%m/%d')
                                if hasattr(date_of_birth, 'strftime')
                                else str(date_of_birth).replace('-', '/')),
                "metadata": meta_data,
            }

            response = bellbank_request('POST', url, headers=headers,
                                        json=payload)

            return response

        except Exception as e:
            # None rather than a jsonify tuple: callers read .status_code off
            # this, or interpolate it into an Authorization header, so a tuple
            # turned a bank outage into an AttributeError or a request sent as
            # 'Bearer (<Response ...>, 500)'.
            print(f'[bellbank] request failed: {type(e).__name__}: {e}')
            return None

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

            response = bellbank_request('GET', url, headers=headers)

            return response

        except Exception as e:
            # None rather than a jsonify tuple: callers read .status_code off
            # this, or interpolate it into an Authorization header, so a tuple
            # turned a bank outage into an AttributeError or a request sent as
            # 'Bearer (<Response ...>, 500)'.
            print(f'[bellbank] request failed: {type(e).__name__}: {e}')
            return None

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

            response = bellbank_request('POST', url, headers=headers,
                                        json=payload)

            return response

        except Exception as e:
            # None rather than a jsonify tuple: callers read .status_code off
            # this, or interpolate it into an Authorization header, so a tuple
            # turned a bank outage into an AttributeError or a request sent as
            # 'Bearer (<Response ...>, 500)'.
            print(f'[bellbank] request failed: {type(e).__name__}: {e}')
            return None

    @staticmethod
    def transfer_outbound(bank_code, amount, narration, account_number, reference, sender_name, recipient_name,
                          access_token):
        """ """

        try:

            url = bellbank_url('transfer')

            # Keyed on the reference, which is unique per transfer. It used to
            # be built from sender, amount, bank, account and recipient, so two
            # genuine transfers of the same amount to the same person produced
            # the same key: BellBank collapses the second into the first, while
            # the caller reads the 200 as success and debits the wallet again.
            # A retry of one transfer reuses its reference and still dedupes.
            idempotency_key = hmac.new(
                config.secret_key.encode(), str(reference).encode(),
                hashlib.sha256).hexdigest()

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

            response = bellbank_request('POST', url, headers=headers,
                                        json=payload)

            return response

        except Exception as e:
            # None rather than a jsonify tuple: callers read .status_code off
            # this, or interpolate it into an Authorization header, so a tuple
            # turned a bank outage into an AttributeError or a request sent as
            # 'Bearer (<Response ...>, 500)'.
            print(f'[bellbank] request failed: {type(e).__name__}: {e}')
            return None

    @staticmethod
    def find_individual_client(access_token, bvn, email_address,
                               page_limit=100, max_pages=20):
        """The BellBank client already created for this customer, or None.

        BellBank can issue an account and we can still fail to save it (a
        database error after their 200). Every retry is then refused, because
        the customer already exists at BellBank, and the account number we were
        given is lost. This finds it again through GET /v1/account/clients.

        BellBank allows one client per email ('Email address already exists'),
        so the email identifies the client. The BVN must also agree whenever
        BellBank returns one that can be compared, so a reused email can never
        attach someone else's account.
        """
        if not bvn or not email_address:
            return None

        wanted_bvn = str(bvn).strip()
        wanted_email = str(email_address).strip().lower()

        headers = {
            'content-type': 'application/json',
            'accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }

        for page in range(1, max_pages + 1):
            url = bellbank_url(
                f'account/clients?accountType=individual'
                f'&page={page}&limit={page_limit}')

            try:
                response = bellbank_request('GET', url, headers=headers)
                body = response.json()
            except Exception as e:
                print(f'[bellbank] client lookup failed: '
                      f'{type(e).__name__}: {e}')
                return None

            clients = _client_list(body)

            # Shapes only, never values: these records hold BVNs and emails.
            if clients is None:
                data = body.get('data') if isinstance(body, dict) else None
                print(f'[bellbank] client lookup: unexpected response '
                      f'(HTTP {getattr(response, "status_code", None)}), '
                      f'top-level keys {_keys(body)}, '
                      f'data is {type(data).__name__} with keys {_keys(data)}')
                return None

            print(f'[bellbank] client lookup page {page}: '
                  f'HTTP {getattr(response, "status_code", None)}, '
                  f'{len(clients)} clients'
                  + (f', record keys {_keys(clients[0])}' if clients else ''))

            for client in clients:
                if not isinstance(client, dict):
                    continue

                email = str(client.get('emailAddress') or '').strip().lower()

                if email != wanted_email or not client.get('accountNumber'):
                    continue

                # BellBank allows one client per email, so the email is what
                # identifies them. The BVN must still agree whenever it is
                # comparable; a masked one (222****221) cannot be compared.
                their_bvn = str(client.get('bvn') or '').strip()

                if their_bvn.isdigit() and their_bvn != wanted_bvn:
                    print('[bellbank] client lookup: email matched but the '
                          'BVN differs, so it is not attached')
                    return None

                return client

            if len(clients) < page_limit:
                print('[bellbank] client lookup: no client with that email')
                return None

        print(f'[bellbank] client lookup stopped after {max_pages} pages')
        return None

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

            response = bellbank_request('GET', url, headers=headers)

            return response

        except Exception as e:
            # None rather than a jsonify tuple: callers read .status_code off
            # this, or interpolate it into an Authorization header, so a tuple
            # turned a bank outage into an AttributeError or a request sent as
            # 'Bearer (<Response ...>, 500)'.
            print(f'[bellbank] request failed: {type(e).__name__}: {e}')
            return None

    @staticmethod
    def client_ip():
        """The address the webhook actually came from.

        Order matters, and X-Forwarded-For is deliberately last of the headers.
        Cloudflare sits in front of this service and *appends* to
        X-Forwarded-For rather than replacing it, so its leftmost entry is
        whatever the caller sent -- anyone can put an allowlisted address there
        and walk through the IP check. CF-Connecting-IP is written by Cloudflare
        and overwrites any client value, so it is the one that cannot be forged
        from outside.

        If this ever runs somewhere without Cloudflare in front, the
        X-Forwarded-For fallback becomes spoofable again and the allowlist stops
        being a real control.
        """
        for header in ('CF-Connecting-IP', 'True-Client-IP'):
            value = request.headers.get(header)

            if value:
                return value.strip()

        forwarded = request.headers.get('X-Forwarded-For', '')

        if forwarded:
            return forwarded.split(',')[0].strip()

        return request.remote_addr

    @staticmethod
    def verify_bellbank_signature(raw_payload):
        """Check the signature, if BellBank sends one.

        Returns True/False when a secret is configured and a signature header
        is present, and None when signature checking is not configured -- which
        lets the caller fall back rather than treat "not configured" as "forged".
        """
        secret = getattr(config, 'bellbank_webhook_secret', None)

        if not secret:
            return None

        header_name = getattr(
            config, 'bellbank_webhook_signature_header', 'X-Signature')
        sent_signature = request.headers.get(header_name)

        if not sent_signature:
            print(f'[bellbank] no {header_name} header on webhook')
            return None

        expected = hmac.new(
            secret.encode(), raw_payload, hashlib.sha256
        ).hexdigest()

        # compare_digest avoids leaking the signature through timing.
        if not hmac.compare_digest(expected, sent_signature.strip()):
            print('[bellbank] webhook rejected: signature mismatch')
            return False

        return True

    @staticmethod
    def verify_bellbank_request(raw_payload):
        """Confirm the request really came from BellBank.

        This endpoint credits customer wallets, so it cannot be authenticated
        with jwt_required -- BellBank has no Payverve JWT to send, which is why
        every collection notification was rejected with 401.

        BellBank does not sign webhooks. Confirmed in the business portal
        (Settings -> API Configuration): the whole webhook configuration, for
        both live and test mode, is a single 'Webhook URL' field. There is no
        signing secret, no signature setting and no IP allowlist there, and
        their public documentation describes no signature either.

        So in practice the IP branch below is the one that runs, and
        BELLBANK_WEBHOOK_IPS has to be set from the addresses BellBank gives
        you. The signature branch is kept because it costs nothing and is the
        better proof if they ever add one. Either is accepted, strongest
        first:

          1. a valid signature, when BELLBANK_WEBHOOK_SECRET is set and they do
             in fact sign -- confirm the header name and scheme with them, and
             prefer this;
          2. otherwise a source address in BELLBANK_WEBHOOK_IPS.

        Fails closed when neither is configured, and a signature that is present
        but wrong is always rejected, never downgraded to the IP check. Without
        this, anyone who learns the URL could POST a forged 'collection' event
        and credit any account number.
        """
        signature_result = BellbankHelper.verify_bellbank_signature(raw_payload)

        if signature_result is True:
            return True

        if signature_result is False:
            # A bad signature is a forgery, not a reason to try something else.
            return False

        allowed = [ip.strip() for ip
                   in (getattr(config, 'bellbank_webhook_ips', '') or '').split(',')
                   if ip.strip()]

        source = BellbankHelper.client_ip()

        if not allowed:
            # The address is logged because it is the only way to learn it.
            # BellBank does not publish the addresses they send from and their
            # portal has no allowlist page, so the first genuine notification to
            # arrive is what tells you what to put in BELLBANK_WEBHOOK_IPS.
            # Rejected either way -- this reports, it does not admit.
            print('[bellbank] webhook rejected: neither '
                  'BELLBANK_WEBHOOK_SECRET (with a signature header) nor '
                  'BELLBANK_WEBHOOK_IPS is configured, so the request cannot '
                  'be shown to be from BellBank. Deposits cannot be credited '
                  'until one is set.')
            print(f'[bellbank] this request came from {source}. If you are '
                  'expecting a deposit right now, that is likely BellBank: '
                  'verify it with them, then set BELLBANK_WEBHOOK_IPS to it.')
            print(f'[bellbank] headers seen: '
                  f'{sorted(request.headers.keys())}')
            return False

        if source not in allowed:
            print(f'[bellbank] webhook rejected: {source} is not in '
                  'BELLBANK_WEBHOOK_IPS')
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
            if not BellbankHelper.verify_bellbank_request(payload):
                return jsonify({
                    'code': 401,
                    'code_message': 'unauthorised',
                    # Not necessarily a signature: BellBank does not sign,
                    # so this is usually an unrecognised source address. The
                    # server log says which check refused and why.
                    'data': 'request could not be verified as coming from '
                            'BellBank'
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

            NotificationResource.store_and_push(
                title="Payverve Transfer",
                body=f"{payverve_wallet.currency_ticker}{float(amount_received): ,.2f} was received from {sender_name} | {sender_account_number}",
                user_id=payverve_wallet.user_id,
                data={"type": "wallet_credit", "amount": amount_received},
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

            NotificationResource.store_and_push(
                title="Local Transfer",
                body=f"₦{float(amount_received): ,.2f} was received from {sender_name} | {sender_account_number}",
                user_id=payverve_wallet.user_id,
                data={"type": "wallet_credit", "amount": amount_received},
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
