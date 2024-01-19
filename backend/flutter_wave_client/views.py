# Create your views here.
# from django.shortcuts import render
# from pyrebase import pyrebase
#
# from backend.core.config.firebase import config
from drf_yasg.utils import swagger_auto_schema
# views.py
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer
from .services import process_payment_transaction


class WalletListCreateView(generics.ListCreateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


class TransactionListCreateView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionDetailView(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionDoubleEntryListCreate(generics.ListCreateAPIView):

    @swagger_auto_schema(
        operation_summary="Perform a flutterwave transfer",
        operation_description="Perform a flutterwave transfer by providing the required fields.",
        tags=["Transfer Management"],
        request_body=TransactionSerializer,
        responses={201: TransactionSerializer(many=False), 400: "Transfer process failed."}
    )
    def post(self, request: Request):
        data = request.data
        owner_id = data.get('owner')
        recepient_id = data.get('recepient')
        currency = data.get('currency')
        amount = data.get('amount')
        narative = data.get('narative')

        included_fields = [owner_id, recepient_id, currency, amount]
        if not all(included_fields):
            bad_response = {
                "status": "failed",
                "message": "All fields are required."
            }
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)

        wallet_from = Wallet.objects.filter(owner_id=owner_id, currency=currency)
        wallet_to = Wallet.objects.filter(owner_id=recepient_id, currency=currency)
        process_payment_transaction(amount, wallet_from, wallet_to, narative)

# firebase = pyrebase.initialize_app(config)
# authentication = firebase.auth()
# database = firebase.database()

# def sign_in(request):
#     return render(request, auth)
#
#
# def home(request):
#     return render(request, "Home.html")
#
#
# def post_sign_in(request):
#     email = request.POST.get('email')
#     pasw = request.POST.get('pass')
#     try:
#         # if there is no error then signin the user with given email and password
#         user = authentication.sign_in_with_email_and_password(email, pasw)
#     except:
#         message = "Invalid Credentials!!Please ChecK your Data"
#         return render(request, "Login.html", {"message": message})
#     session_id = user['idToken']
#     request.session['uid'] = str(session_id)
#     return render(request, "Home.html", {"email": email})
#
#
# def logout(request):
#     try:
#         del request.session['uid']
#     except:
#         pass
#     return render(request, "Login.html")
#
#
# def sign_up(request):
#     return render(request, "Registration.html")
#
#
# def post_sign_up(request):
#     email = request.POST.get('email')
#     passwd = request.POST.get('pass')
#     name = request.POST.get('name')
#     try:
#         # creating a user with the given email and password
#         user = authentication.create_user_with_email_and_password(email, passwd)
#         uid = user['localId']
#         idtoken = request.session['uid']
#         print(uid)
#     except:
#         return render(request, "Registration.html")
#     return render(request, "Login.html")
