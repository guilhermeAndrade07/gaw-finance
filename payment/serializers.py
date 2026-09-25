from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from app.mixins import UserScopedSerializerMixin
from categories.models import Category
from payment.models import CreditCard, Invoice, Payment
from payment.services import assign_invoice_to_payment, register_payment


class InvoiceSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {'card': CreditCard}
    total = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ['id', 'card', 'closing_date', 'due_date', 'status', 'total']
        read_only_fields = ['user', 'total']

    def get_total(self, obj):
        return str(obj.total)


class PaymentSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {
        'card': CreditCard,
        'category': Category,
    }

    class Meta:
        model = Payment
        fields = ['id', 'card', 'name', 'description', 'category', 'date_payment', 'value', 'parcelas', 'paid', 'invoice']
        read_only_fields = ['user', 'invoice']
        extra_kwargs = {
            'card': {'required': True, 'allow_null': False},
        }

    def validate_parcelas(self, value):
        if value < 1 or value > 60:
            raise serializers.ValidationError('O numero de parcelas deve estar entre 1 e 60.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        try:
            return register_payment(
                user=request.user,
                card=validated_data['card'],
                name=validated_data['name'],
                description=validated_data.get('description'),
                category=validated_data.get('category'),
                date_payment=validated_data['date_payment'],
                value=validated_data['value'],
                parcelas=validated_data.get('parcelas', 1),
                paid=validated_data.get('paid', False),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.card_id and instance.date_payment:
            assign_invoice_to_payment(instance)
        return instance
