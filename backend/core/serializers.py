from rest_framework import serializers

from .models import Wallet, Transaction, Transfer, TransferAdditionalInformation


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'  # ('id', 'balance', 'email', 'message')


class WalletTopUpSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(required=True, min_value=0, decimal_places=4, max_digits=15)

    class Meta:
        model = Wallet
        fields = ('id', 'amount')


class TransferSerializer(serializers.ModelSerializer):
    # wallet = WalletSerializer(many=True)
    narration = serializers.CharField(required=False)
    option = serializers.ChoiceField(choices=['PayVerve', 'Other Banks'])

    class Meta:
        model = Transfer
        fields = ('id', 'amount', 'option', 'account_number', 'narration')


class TransferAdditionalInformationSerializer(serializers.ModelSerializer):
    transfer = TransferSerializer

    class Meta:
        model = TransferAdditionalInformation
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
