from banks.models import Bank
from rest_framework import serializers

from .models import InvestmentAsset, InvestmentMovement


class InvestmentAssetSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['bank'].queryset = Bank.objects.filter(user=request.user) if request else Bank.objects.none()

    class Meta:
        model = InvestmentAsset
        fields = ['id', 'name', 'asset_type', 'subtype', 'institution', 'bank', 'maturity_date', 'expected_rate', 'liquidity_type', 'current_value', 'notes', 'is_active']
        read_only_fields = ['user']


class InvestmentMovementSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['asset'].queryset = InvestmentAsset.objects.filter(user=request.user) if request else InvestmentAsset.objects.none()

    class Meta:
        model = InvestmentMovement
        fields = ['id', 'asset', 'operation_type', 'value', 'movement_date', 'register_cash_flow', 'notes']
        read_only_fields = ['user']
