# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .config.authentication import FirebaseAuthentication
from .models import Account, Transaction
from .serializers import AccountSerializer, TransactionSerializer


class AccountListCreate(generics.ListCreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class TransactionListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    """Here just add FirebaseAuthentication class in authentication_classes"""
    authentication_classes = [FirebaseAuthentication]

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


