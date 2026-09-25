from rest_framework import serializers

from app.mixins import UserScopedSerializerMixin
from banks.models import Bank
from categories.models import Category
from outflows.models import Outflow
from outflows.services import register_outflow


class OutflowSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {
        'bank': Bank,
        'category': Category,
    }

    class Meta:
        model = Outflow
        fields = ['id', 'title', 'bank', 'category', 'value']
        read_only_fields = ['user']

    def create(self, validated_data):
        return register_outflow(
            user=self.context['request'].user,
            bank=validated_data['bank'],
            value=validated_data['value'],
            title=validated_data.get('title'),
            category=validated_data.get('category'),
        )
