from rest_framework import serializers

from app.mixins import UserScopedSerializerMixin
from categories.models import Category
from payment.models import CreditCard
from .models import Signature


class SignatureSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {
        'credit_card': CreditCard,
        'category': Category,
    }

    class Meta:
        model = Signature
        fields = ['id', 'name', 'description', 'value', 'billing_day', 'is_active', 'credit_card', 'category']
        read_only_fields = ['user']
