from django.contrib.auth.models import User
from django.db import models

from .utils.Currency import Currency
from .utils.TransactionStatus import TransactionStatus


# Create your models here.
class PayverveUser(User):
    fullname = User.first_name, ' ', User.last_name


class Account(models.Model):
    naira_balance = models.DecimalField(decimal_places=4, max_digits=15)
    dollar_balance = models.DecimalField(decimal_places=4, max_digits=15)
    pound_balance = models.DecimalField(decimal_places=4, max_digits=15)
    owner = models.ForeignKey(User, related_name='owner', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     abstract: True


# class NairaAccount(Account):
#     currency = Currency.Naira
#
#
# class DollarAccount(Account):
#     currency = Currency.Dollar
#
#
# class PoundAccount(Account):
#     currency = Currency.Pound


class Transaction(models.Model):
    transaction_datetime = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=10, choices=Currency.choices(), default=Currency.Naira)
    acc_from = models.ForeignKey(Account, related_name='account_from', on_delete=models.CASCADE)
    acc_to = models.ForeignKey(Account, related_name='account_to', on_delete=models.CASCADE)
    balance = models.DecimalField(decimal_places=4, max_digits=15)
    transaction_status = models.CharField(max_length=15, choices=TransactionStatus.choices())
    # created_at = models.DateTimeField(auto_now_add=True)
