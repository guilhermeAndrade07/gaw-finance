from rest_framework import serializers

from app.mixins import UserScopedSerializerMixin
from banks.models import Bank

from .models import InvestmentAsset, InvestmentMovement


class InvestmentAssetSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {'bank': Bank}

    class Meta:
        model = InvestmentAsset
        fields = ['id', 'name', 'asset_type', 'subtype', 'institution', 'bank', 'maturity_date', 'expected_rate', 'liquidity_type', 'current_value', 'notes', 'is_active']
        read_only_fields = ['user']


class InvestmentMovementSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {'asset': InvestmentAsset}

    class Meta:
        model = InvestmentMovement
        fields = ['id', 'asset', 'operation_type', 'value', 'movement_date', 'register_cash_flow', 'notes']
        read_only_fields = ['user']
