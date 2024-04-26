# Create your models here.
from django.db import models


class Wallet(models.Model):
    # balance, userId, timestamps
    pass


class WalletTransaction(models.Model):
    # amount, userId, isInflow(isDebit), paymentMethod, currency, status, timestamps
    pass


class Account(models.Model):
    """
    This is the user wallet.
    """
    name = models.CharField(max_length=255)

    def get_balance(self):
        debit_total = self.transactionentry_set.filter(is_debit=True).aggregate(models.Sum('amount'))[
                          'amount__sum'] or 0
        credit_total = self.transactionentry_set.filter(is_debit=False).aggregate(models.Sum('amount'))[
                           'amount__sum'] or 0
        return credit_total - debit_total

    def get_transaction_history(self):
        return self.transactionentry_set.all()


class Transaction(models.Model):
    # userId, transactionId, name, email, phone, amount, currency, paymentStatus, paymentGateway, timestamps
    description = models.CharField(max_length=255)
    date = models.DateField()


class TransactionEntry(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_debit = models.BooleanField()

# class User:
#     # first_name: {type: String, default: null},
#     # last_name: {type: String, default: null},
#     # email: {type: String, unique: true},
#     # password:
#     pass
