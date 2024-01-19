# Your transaction processing logic
import decimal

from django.utils import timezone

from .models import Transaction, TransactionEntry, Account


def process_payment_transaction(amount: decimal, sender_account: Account, receiver_account: Account, description):
    # Assuming you have Account instances for sender and receiver

    # Create a new transaction
    transaction = Transaction.objects.create(description=description, date=timezone.now())

    # Create debit entry for the sender's account
    TransactionEntry.objects.create(
        transaction=transaction,
        account=sender_account,
        amount=-amount,  # negative amount for debit
        is_debit=True
    )

    # Create credit entry for the receiver's account
    TransactionEntry.objects.create(
        transaction=transaction,
        account=receiver_account,
        amount=amount,
        is_debit=False
    )
