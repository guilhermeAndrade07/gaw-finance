from rest_framework import serializers

from app.mixins import UserScopedSerializerMixin
from banks.models import Bank
from inflows.models import Inflow
from inflows.services import register_inflow


class InflowSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {'bank': Bank}

    class Meta:
        model = Inflow
        fields = ['id', 'title', 'bank', 'value']
        read_only_fields = ['user']

    def create(self, validated_data):
        return register_inflow(
            user=self.context['request'].user,
            bank=validated_data['bank'],
            value=validated_data['value'],
            title=validated_data.get('title'),
        )
