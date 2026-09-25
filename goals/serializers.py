from rest_framework import serializers

from app.mixins import UserScopedSerializerMixin
from categories.models import Category
from goals.models import MonthlyGoal


class MonthlyGoalSerializer(UserScopedSerializerMixin, serializers.ModelSerializer):
    user_scoped_fields = {'category': Category}

    class Meta:
        model = MonthlyGoal
        fields = ['id', 'category', 'value', 'month', 'year']
        read_only_fields = ['user']
