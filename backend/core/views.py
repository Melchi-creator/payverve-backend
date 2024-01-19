# Create your views here.
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status  # , status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .config.authentication import FirebaseAuthentication
from .models import Wallet, Transaction, TransferAdditionalInformation, Transfer
from .serializers import WalletSerializer, TransactionSerializer, TransferAdditionalInformationSerializer, \
    TransferSerializer
from .services import process_payment_transfer, initiate_bank_transfer, get_exchange_rate


# from rest_framework.response import Response


class WalletListCreate(generics.ListCreateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

    def perform_create(self, serializer):
        owner_id = self.request.data.get('owner')
        currency = self.request.data.get('currency')
        wallet = Wallet.objects.filter(owner_id=owner_id, currency=currency)
        # print(f'Wallet count: {wallet.count()}')
        if wallet.count() > 0:
            print(f'Wallet count: {wallet.count()}')
            bad_response = {"status": "failed", "message": "Wallet already exists!"}
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(f'Wallet count else: {wallet.count()}')
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

    def perform_create(self, serializer):
        wallet = self.kwargs['wallet']


class TransfersListByOwner(generics.ListAPIView):
    serializer_class = TransferSerializer
    lookup_field = 'wallet'

    def get_queryset(self):
        wallet_id = self.kwargs['wallet']  # self.request.get('pk', None)
        # filter query set based on the wallet => pk (try filer by owner)
        return Transfer.objects.filter(wallet_id=wallet_id)


class TransferAdditionalInformationListCreate(generics.ListCreateAPIView):
    queryset = TransferAdditionalInformation.objects.all()
    serializer_class = TransferAdditionalInformationSerializer


class TransactionListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    """Here just add FirebaseAuthentication class in authentication_classes"""
    authentication_classes = [FirebaseAuthentication]

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransferListCreate2(APIView):
    @swagger_auto_schema(
        operation_summary="Create a new  transfer",
        operation_description="Create a transfer providing the required fields.",
        tags=["Wallet Transfers"], request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'wallet': openapi.Schema(type=openapi.TYPE_INTEGER, description='Wallet id for the transferor'),
                'account_number': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='Account number for the transferee'),
                'amount': openapi.Schema(type=openapi.TYPE_STRING, description='Amount to transfer'),
                'option': openapi.Schema(type=openapi.TYPE_STRING, description='Transfer option, \'PayVerve\' or '
                                                                               '\'Other Banks\''),
                'narration': openapi.Schema(type=openapi.TYPE_STRING, description='Narration for the transfer'),
                'type': openapi.Schema(type=openapi.TYPE_STRING,
                                       description='Type of transfer, \'Local\' or \'Foreign\''),
                'bank_name': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='Recepient\'s bank if \'Other Bank\' is selected'),
                'country': openapi.Schema(type=openapi.TYPE_STRING,
                                          description='Recepient\'s country if \'Foreign\' is selected'),
                'bank_swift': openapi.Schema(type=openapi.TYPE_STRING, description='Recepient\'s bank swift code')
            },
            required=['wallet', 'account_number', 'amount']
        ),
        responses={201: TransferSerializer(many=False), 400: "Transfer failed."}
    )
    def post(self, request):
        data = request.data
        print(f'Payload data: {data}')

        transfer = process_payment_transfer(data)
        # included_fields = [email, password, first_name, last_name]
        # Check if any of the required fields are missing
        if transfer is None:
            bad_response = {
                "status": "failed",
                "message": "Could not transfer the amount."
            }
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)

        response = {
            "status": "success",
            "message": "User created successfully.",
            "data": transfer
        }
        return Response(response, status=status.HTTP_201_CREATED)


class WalletListCreateView(generics.ListCreateAPIView):  # TODO: Remove reduntant view (defined above)
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


class WalletToWalletTransferView(generics.UpdateAPIView):
    serializer_class = WalletSerializer

    # queryset = Wallet.objects.all()
    # def

    def update(self, request, *args, **kwargs):
        # self.serializer_class = WalletSerializer
        pk = self.kwargs['pk']
        sender_wallet = Wallet.objects.get(pk=pk)  # self.get_object()
        receiver_wallet_id = self.kwargs['receiver_wallet_id']
        receiver_wallet = Wallet.objects.get(id=receiver_wallet_id)

        amount = request.data.get('amount', 0)

        # Check if the sender has enough balance
        if sender_wallet.balance < amount:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        # Implement the logic to deduct from sender and credit to receiver
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount
        sender_wallet.save()
        receiver_wallet.save()

        return Response({'success': 'Transfer successful.'})


class WalletToBankTransferView(generics.CreateAPIView):
    serializer_class = WalletSerializer
    queryset = Wallet.objects.all()

    def create(self, request, *args, **kwargs):
        sender_wallet = self.get_object()

        amount = request.data.get('amount', 0)
        bank_account_number = request.data.get('bank_account_number')
        bank_code = request.data.get('bank_code')

        # Check if the sender has enough balance
        if sender_wallet.balance < amount:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        # Implement the logic to initiate a bank transfer
        response = initiate_bank_transfer(amount, bank_account_number, bank_code, sender_wallet.currency)

        # Check the response for success or failure and handle accordingly
        # TODO: reduce sender wallet by amount

        if response.status == 200:
            sender_wallet.balance -= amount
            sender_wallet.save()
            serializer = WalletSerializer(sender_wallet)
            extra_data = {
                "wallet_info": serializer.data,
                "amount": amount,
                "bank_account_number": bank_account_number,
                "bank_code": bank_code
            }
            response = {
                "status": "success",
                "message": "Transfered amount successfully.",
                "data": extra_data
            }
        else:
            return Response({'error': 'Could not complete bank transfer.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response, status=status.HTTP_201_CREATED)


def get_currency_exchange_rate(request, base_currency, target_currency):
    response = get_exchange_rate(base_currency, target_currency)
    return Response(response, status=status.HTTP_200_OK)
