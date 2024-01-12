from rest_framework import serializers

from .models import Wallet, Transaction, Transfer, TransferAdditionalInformation


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'  # ('id', 'balance', 'email', 'message')


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = '__all__'


class TransferAdditionalInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferAdditionalInformation
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
