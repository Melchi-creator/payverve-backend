from django.urls import path

from .views import (WalletListCreate, UserWalletRetrieve,
                    TransferListCreate2, WalletToWalletTransferView, WalletToBankTransferView,
                    get_currency_exchange_rate, WalletTopUpView, CurrencyExchangeRateView)

urlpatterns = [
    path('wallets/', WalletListCreate.as_view(), name="api-wallets"),
    # path('wallet/<int:pk>/', WalletRetrieveUpdate.as_view(), name="api-wallet"),
    path('wallets/<int:pk>/', WalletTopUpView.as_view(), name="api-wallet-top-up"),
    path('wallets/<uuid:owner>/', UserWalletRetrieve.as_view(), name="api-user-wallet"),
    # path('transfers/', TransferListCreate.as_view(),  name="api-transfers"),
    # path('transfer-details/', TransferAdditionalInformationListCreate.as_view(),  name="api-transfer-details"),
    path('transfer/', TransferListCreate2.as_view(), name="api-transfer"),

    # TODO: transfers by owner
    # path('transfers/<int:pk>/', TransfersListByOwner.as_view(), name="api-transfers-by-owner"),
    # search transactions by wallet owner id

    # Transfer and Flutterwave APIs
    # path('wallets/', WalletListCreateView.as_view(), name='wallet-list-create'), # TODO: already impemented above
    path('wallets/transfer/<int:pk>/wallet/', WalletToWalletTransferView.as_view(),
         name='wallet-to-wallet-transfer'),
    path('wallets/transfer/<int:pk>/bank/', WalletToBankTransferView.as_view(),
         name='wallet-to-bank-transfer'),
    # path('wallet-to-wallet/<int:sender_wallet_id>/<int:receiver_wallet_id>/<decimal:amount>/',
    # initiate_wallet_to_wallet_transfer, name='wallet-to-wallet-transfer'),
    # path('wallet-to-bank/<int:sender_wallet_id>/<decimal:amount>/<str:bank_account_number>/<str:bank_code>/',
    # initiate_wallet_to_bank_transfer, name='wallet-to-bank-transfer'),
    path('exchange-rate/',
         CurrencyExchangeRateView.as_view(),
         name='currency-exchange-rate'
         ),

]
