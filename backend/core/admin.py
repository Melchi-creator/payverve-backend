from django.contrib import admin

from .models import Transaction, Account  # , PoundAccount, NairaAccount, DollarAccount

# Register your models here.

admin.site.register(Transaction)
admin.site.register(Account)
