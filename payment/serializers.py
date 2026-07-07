from categories.models import Category
from rest_framework import serializers
from payment.models import CreditCard, Invoice, Payment


class InvoiceSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ['id', 'card', 'closing_date', 'due_date', 'status', 'total']
        read_only_fields = ['user', 'total']

    def get_total(self, obj):
        return str(obj.total)


class PaymentSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['category'].queryset = Category.objects.filter(user=request.user) if request else Category.objects.none()
        self.fields['card'].queryset = CreditCard.objects.filter(user=request.user) if request else CreditCard.objects.none()
        if request:
            self.fields['invoice'].queryset = Invoice.objects.filter(user=request.user)
        else:
            self.fields['invoice'].queryset = Invoice.objects.none()

    class Meta:
        model = Payment
        fields = ['id', 'card', 'name', 'description', 'category', 'date_payment', 'value', 'parcelas', 'paid', 'invoice']
        read_only_fields = ['user', 'invoice']
        extra_kwargs = {
            'card': {'required': True, 'allow_null': False},
        }
