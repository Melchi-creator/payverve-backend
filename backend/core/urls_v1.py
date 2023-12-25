from django.urls import path

from .views import WalletListCreate, TransactionListCreate, TransferListCreate, TransferAdditionalInformationListCreate, \
    WalletRetrieveUpdate, UserWalletRetrieve

urlpatterns = [
    path('wallets/', WalletListCreate.as_view(), name="api-wallets"),
    path('wallet/<int:pk>/', WalletRetrieveUpdate.as_view(), name="api-wallet"),
    path('wallets/<int:owner>/', UserWalletRetrieve.as_view(), name="api-user-wallet"),
    path('transfers/', TransferListCreate.as_view(),  name="api-transfers"),
    path('transfer-details/', TransferAdditionalInformationListCreate.as_view(),  name="api-transfer-details"),
    path('transactions/', TransactionListCreate.as_view(),  name="api-transactions"),
]
