from django.contrib import admin

from .models import Transaction, Wallet, Transfer, \
    TransferAdditionalInformation  # , PoundAccount, NairaAccount, DollarAccount

# Register your models here.

admin.site.register(Transaction)
admin.site.register(Wallet)
admin.site.register(Transfer)
admin.site.register(TransferAdditionalInformation)
