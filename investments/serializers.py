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
        fields = '__all__'
        read_only_fields = ['user']


class InvestmentMovementSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['asset'].queryset = InvestmentAsset.objects.filter(user=request.user) if request else InvestmentAsset.objects.none()

    class Meta:
        model = InvestmentMovement
        fields = '__all__'
        read_only_fields = ['user']
