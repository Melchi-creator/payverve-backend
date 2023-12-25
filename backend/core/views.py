# Create your views here.
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .config.authentication import FirebaseAuthentication
from .models import Wallet, Transaction, TransferAdditionalInformation, Transfer
from .serializers import WalletSerializer, TransactionSerializer, TransferAdditionalInformationSerializer, \
    TransferSerializer


class WalletListCreate(generics.ListCreateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

    def perform_create(self, serializer):
        owner_id = self.request.data.get('owner')
        currency = self.request.data.get('currency')
        print(owner_id, currency)
        wallet = Wallet.objects.filter(owner_id=owner_id, currency=currency)
        # get_object_or_404(Wallet, owner_id=owner_id, currency=currency)
        if wallet.count() > 0:
            print('Wallet count: ', wallet.count())
            # return Response("Wallet already exists!", status=status.HTTP_400_BAD_REQUEST)
            raise ValidationError("Wallet already exists!")
        return serializer.save()


class WalletRetrieveUpdate(generics.RetrieveUpdateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


class UserWalletRetrieve(generics.ListAPIView):
    # queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    lookup_field = 'owner'

    def get_queryset(self):
        owner_id = self.kwargs['owner']  # self.request.get('pk', None)
        # filter query set based on the user_id => pk
        return Wallet.objects.filter(owner_id=owner_id)


class TransferListCreate(generics.ListCreateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer


class TransferAdditionalInformationListCreate(generics.ListCreateAPIView):
    queryset = TransferAdditionalInformation.objects.all()
    serializer_class = TransferAdditionalInformationSerializer


class TransactionListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    """Here just add FirebaseAuthentication class in authentication_classes"""
    authentication_classes = [FirebaseAuthentication]

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
