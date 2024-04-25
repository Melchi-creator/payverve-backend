# urls.py
from django.urls import path

from .views import TransactionDoubleEntryListCreate

urlpatterns = [
    # path('wallets/', WalletListCreateView.as_view(), name='wallet-list-create'),
    # path('transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    # path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),

    path('transfer/', TransactionDoubleEntryListCreate.as_view(), name='flutterwave-transfer-create'),
]
