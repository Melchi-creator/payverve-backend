# services.py

from decimal import Decimal

import requests
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Transaction, Wallet, Transfer, TransferAdditionalInformation


@receiver(pre_save, sender=Transaction)
def validate_transaction(sender, instance, **kwargs):
    # Add your validation logic here
    # For example, check if the transaction meets certain criteria
    # If not, raise an exception to prevent saving
    print("%s, %s" % (sender, instance))


def get_wallet_by_account_number(account_number: str):
    wallet = Wallet.objects.get(account_number=account_number)
    # print(f'Wallet: {wallet}')
    return wallet


def process_payment_transfer(payload):
    # Assuming you have Wallet instances for sender and receiver if within PayVerve
    wallet_id = int(payload['wallet'])
    amount = Decimal(payload['amount'])
    option = payload['option']
    # sender_wallet = WalletSerializer.__getitem__(key=wallet_id)
    sender_wallet = Wallet.objects.get(pk=wallet_id)  # filter(id=payload['wallet'])
    if sender_wallet is None:
        raise Exception("The sender does not exist!")
    print(f'Sennder wallet: {sender_wallet}')
    if option == "PayVerve":
        # Validate account number provided
        recepient = get_wallet_by_account_number(payload['account_number'])
        print(f'Recepient: {recepient}')
        # Create a new transfer
        transfer = Transfer.objects.create(
            wallet=sender_wallet,
            option=option,
            account_number=payload['account_number'],
            amount=amount,
            narration=payload['narration']
        )
        print(f'Transfer: {transfer}')
        return transfer
    elif option == "Other Banks":
        # Create a new transfer with additional details
        transfer = Transfer.objects.create(
            wallet=sender_wallet,
            option=option,
            account_number=payload['account_number'],
            amount=amount,
            narration=payload['narration']
        )

        # Create entry for the additional details
        TransferAdditionalInformation.objects.create(
            transfer=transfer,
            bank_name=payload['bank_name'],
            country=payload['country'],
            bank_swift=payload['bank_swift'],
            type=payload['type'],
            exchange_rate=0
        )
        return transfer


FLUTTERWAVE_API_KEY = settings.FLUTTERWAVE_SECRET_KEY
FLUTTERWAVE_BASE_URL = 'https://api.flutterwave.com/v3'
REDIRECT_URL = 'http://localhost:8001'


def initiate_bank_transfer(amount, bank_account_number, bank_code, currency):
    url = f"{FLUTTERWAVE_BASE_URL}/transfers"
    headers = {
        'Authorization': f'Bearer {FLUTTERWAVE_API_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'tx_ref': 'unique_transaction_reference',
        'amount': amount,
        'currency': currency,
        'recipient': {
            'account_number': bank_account_number,
            'bank_code': bank_code,
            'currency': currency,
        },
        'redirect_url': REDIRECT_URL,
        'order_id': 'order_id',
        'payment_type': 'bank_transfer',
    }

    response = requests.post(url, json=data, headers=headers)
    return response.json()


def get_exchange_rate(base_currency, target_currency):
    url = f"{FLUTTERWAVE_BASE_URL}/rates?base={base_currency}&symbols={target_currency}"
    headers = {
        'Authorization': f'Bearer {FLUTTERWAVE_API_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url, headers=headers)
    return response.json()
