# from django.contrib.auth.models import User
import backend.settings as settings
from auditlog.models import AuditlogHistoryField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from .utils.Currency import Currency
from .utils.TransactionStatus import TransactionStatus


# from backend.accounts.models import User


# Create your models here.

# TODO: add timestamps for all tables.

class Wallet(models.Model):
    balance = models.DecimalField(decimal_places=4, max_digits=15, default=0)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='wallets', on_delete=models.SET(0))
    currency = models.CharField(max_length=20, choices=Currency.choices(), default=Currency.Naira)
    account_number = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    history = AuditlogHistoryField()

    def __str__(self):
        username = str(self.owner).split('@')[0]
        return f"{username}'s {self.currency} Wallet"


class Transfer(models.Model):
    class TransferOption(models.TextChoices):
        PAYVERVE = 'PayVerve'
        OTHER_BANKS = 'Other Banks'

    wallet = models.ForeignKey(Wallet, on_delete=models.SET(0), related_name='transfers')
    option = models.CharField(max_length=20, choices=TransferOption.choices, default=TransferOption.PAYVERVE)
    account_number = models.CharField(max_length=50)
    amount = models.DecimalField(decimal_places=4, max_digits=15)
    narration = models.CharField(max_length=255, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_dt = models.DateTimeField(auto_now=True)
    history = AuditlogHistoryField()

    # option = models.ForeignKey(TransferOption, on_delete=models.CASCADE)

    # def __str__(self):
    #   return f'Transfer: {self.wallet}, {self.amount}, {self.account_number}'

    def get_additional_details(self):
        return self.transferadditionalinformation_set.all()


class TransferAdditionalInformation(models.Model):
    class TransferType(models.TextChoices):
        LOCAL = 'Local'
        FOREIGN = 'Foreign'

    bank_name = models.CharField(max_length=50, null=False, default="ECO BANK")
    country = CountryField(null=False, default="Nigeria")
    bank_swift = models.CharField(max_length=50, null=True)
    transfer = models.ForeignKey(Transfer, on_delete=models.SET(0), null=True)
    type = models.CharField(max_length=15, choices=TransferType.choices, null=False, default=TransferType.LOCAL)
    exchange_rate = models.DecimalField(decimal_places=4, max_digits=15, default=1.0)

    class Meta:
        db_table = 'core_transfer_additional_information'
        verbose_name = _('core_transfer_additional_information')


class Transaction(models.Model):
    transaction_datetime = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(decimal_places=4, max_digits=15)
    transaction_status = models.CharField(max_length=15, choices=TransactionStatus.choices())
    transfer = models.ForeignKey(Transfer, default=None, on_delete=models.SET(0), related_name='transactions')
    # currency = models.CharField(max_length=10, choices=Currency.choices(), default=Currency.Naira)
    # acc_from = models.ForeignKey(Wallet, related_name='account_from', on_delete=models.CASCADE)
    # acc_to = models.ForeignKey(Wallet, related_name='account_to', on_delete=models.CASCADE)


class CurrencyExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3)  # USD, for example
    target_currency = models.CharField(max_length=3)  # GBP, NGN, etc.
    rate = models.DecimalField(max_digits=10, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.base_currency}/{self.target_currency}: {self.rate}"


class UtilityPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='utility_payments', on_delete=models.SET_NULL, null=True)
    account_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)


# class Utility:
#     class UtilityType(models.TextChoices):
#         Airtime = 'Local'
#         Data = 'Foreign'
#         Elec = 'Foreign'
#         Betting = 'Foreign'
#         Transportation = 'Foreign'
#         CableTv = 'Foreign'
#
#     utility_type = models.CharField(max_length=15, choices=UtilityType.choices, null=False,
#     default=UtilityType.Airtime)
# service_provider =
# amount =
# identifier =
# package:
# aditional_info =
