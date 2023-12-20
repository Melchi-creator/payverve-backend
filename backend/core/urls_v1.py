from django.urls import path

from .views import AccountListCreate, TransactionListCreate

urlpatterns = [
    path('accounts/', AccountListCreate.as_view(),  name="api-account"),
    path('transactions/', TransactionListCreate.as_view(),  name="api-transactions"),
]
