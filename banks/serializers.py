from rest_framework import serializers
from banks.models import Bank


class BankSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bank
        fields = ['id', 'name', 'account_type', 'agency', 'account', 'initial_balance', 'balance']
        read_only_fields = ['user', 'balance']
