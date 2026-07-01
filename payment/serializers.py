from categories.models import Category
from rest_framework import serializers
from payment.models import CreditCard, Payment


class PaymentSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['category'].queryset = Category.objects.filter(user=request.user) if request else Category.objects.none()
        self.fields['card'].queryset = CreditCard.objects.filter(user=request.user) if request else CreditCard.objects.none()

    class Meta:
        model = Payment
        fields = ['id', 'card', 'name', 'description', 'category', 'date_payment', 'value', 'parcelas', 'paid']
        read_only_fields = ['user']
        extra_kwargs = {
            'card': {'required': True, 'allow_null': False},
        }
