# from django.contrib.auth.models import User
import accounts.models as accounts
import backend.settings as settings
from django.db import models
from django_countries.fields import CountryField

from .utils.Currency import Currency
from .utils.TransactionStatus import TransactionStatus


# from backend.accounts.models import User


# Create your models here.
class PayverveUser(accounts.User):
    # fullname = User.first_name, ' ', User.last_name
    pass


class Wallet(models.Model):
    balance = models.DecimalField(decimal_places=4, max_digits=15, default=0)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='wallets', on_delete=models.SET(0))
    currency = models.CharField(max_length=20, choices=Currency.choices(), default=Currency.Naira)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s: %s' % (str(self.owner.username), self.currency)


class Transfer(models.Model):
    class TransferOption(models.TextChoices):
        PAYVERVE = 'PayVerve'
        OTHER_BANKS = 'Other Banks'

    wallet = models.ForeignKey(Wallet, on_delete=models.SET(0), related_name='transfers')
    option = models.CharField(max_length=20, choices=TransferOption.choices, default=TransferOption.PAYVERVE)
    account_number = models.CharField(max_length=15)
    amount = models.DecimalField(decimal_places=4, max_digits=15)
    narration = models.CharField(max_length=255)
    # option = models.ForeignKey(TransferOption, on_delete=models.CASCADE)


class TransferAdditionalInformation(models.Model):
    class TransferType(models.TextChoices):
        LOCAL = 'Local'
        FOREIGN = 'Foreign'

    bank_name = models.CharField(max_length=50, null=False, default="ECO BANK")
    country = CountryField(null=False, default="Nigeria")
    bank_swift = models.CharField(max_length=50, null=True)
    type = models.CharField(max_length=15, choices=TransferType.choices, null=False, default=TransferType.LOCAL)
    exchange_rate = models.DecimalField(decimal_places=4, max_digits=15)


class Transaction(models.Model):
    transaction_datetime = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(decimal_places=4, max_digits=15)
    transaction_status = models.CharField(max_length=15, choices=TransactionStatus.choices())
    transfer = models.ForeignKey(Transfer, default=None, on_delete=models.SET(0), related_name='transactions')
    # currency = models.CharField(max_length=10, choices=Currency.choices(), default=Currency.Naira)
    # acc_from = models.ForeignKey(Wallet, related_name='account_from', on_delete=models.CASCADE)
    # acc_to = models.ForeignKey(Wallet, related_name='account_to', on_delete=models.CASCADE)
