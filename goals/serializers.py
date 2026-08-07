from rest_framework import serializers

from goals.models import MonthlyGoal


class MonthlyGoalSerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthlyGoal
        fields = ['id', 'category', 'value', 'month', 'year']
        read_only_fields = ['user']
