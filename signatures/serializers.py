from categories.models import Category
from payment.models import CreditCard
from rest_framework import serializers
from .models import Signature


class SignatureSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            self.fields['credit_card'].queryset = CreditCard.objects.filter(user=request.user)
            self.fields['category'].queryset = Category.objects.filter(user=request.user)
        else:
            self.fields['credit_card'].queryset = CreditCard.objects.none()
            self.fields['category'].queryset = Category.objects.none()

    class Meta:
        model = Signature
        fields = ['id', 'name', 'description', 'value', 'billing_day', 'is_active', 'credit_card', 'category']
        read_only_fields = ['user']
