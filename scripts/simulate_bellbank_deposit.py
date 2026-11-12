"""Pretend BellBank sent a deposit notification to a LOCAL server.

Posts the 'collection' event from BellBank's webhook docs to
/bellbank/webhook, so crediting can be tested end to end -- wallet balance,
transaction row, duplicate handling -- without moving any money.

Local only: it refuses any host but localhost. The server must have
127.0.0.1 in BELLBANK_WEBHOOK_IPS (sample.env.sandbox does), or the webhook
rejects it like any unknown sender.

    # credit N500 to a virtual account in the local database
    python scripts/simulate_bellbank_deposit.py 1000137010 500

    # send the same notification twice: the second must not credit again
    python scripts/simulate_bellbank_deposit.py 1000137010 500 --repeat 2
"""
import argparse
import json
import secrets
import sys
import time
from urllib.parse import urlparse

import requests

LOCAL_HOSTS = ('localhost', '127.0.0.1', '::1')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('account_number',
                        help='the virtual account being paid')
    parser.add_argument('amount', help='naira, e.g. 500')
    parser.add_argument('--url',
                        default='http://127.0.0.1:10000/bellbank/webhook')
    parser.add_argument('--fee', default='0',
                        help='transactionFee BellBank charged')
    parser.add_argument('--sender-name', default='Sandbox Sender')
    parser.add_argument('--sender-account', default='0123456789')
    parser.add_argument('--repeat', type=int, default=1,
                        help='send the identical notification this many times')
    args = parser.parse_args()

    if urlparse(args.url).hostname not in LOCAL_HOSTS:
        parser.error('only a local server can be sent a simulated deposit')

    amount = float(args.amount)
    fee = float(args.fee)
    stamp = int(time.time() * 1000)
    session_id = f'SIM{stamp}{secrets.randbelow(10 ** 9):09d}'

    payload = {
        'event': 'collection',
        'reference': f'SIM_{stamp}',
        'virtualAccount': args.account_number,
        'externalReference': f'SIM-EXT-{stamp}',
        'amountReceived': f'{amount:.2f}',
        'transactionFee': fee,
        'netAmount': amount - fee,
        'stampDuty': 0,
        'sessionId': session_id,
        'sourceCurrency': 'NGN',
        'sourceAccountNumber': args.sender_account,
        'sourceAccountName': args.sender_name,
        'sourceBankCode': '0001',
        'sourceBankName': 'Sandbox Bank',
        'remarks': 'simulated deposit',
        'destinationCurrency': 'NGN',
        'status': 'successful',
        'createdAt': stamp,
        'updatedAt': stamp,
    }

    print(f'sessionId {session_id}')

    for attempt in range(1, args.repeat + 1):
        response = requests.post(args.url, data=json.dumps(payload),
                                 headers={'Content-Type': 'application/json'},
                                 timeout=30)
        print(f'attempt {attempt}: HTTP {response.status_code} '
              f'{response.text[:300]}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
