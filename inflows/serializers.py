from banks.models import Bank
from rest_framework import serializers
from inflows.models import Inflow


class InflowSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['bank'].queryset = Bank.objects.filter(user=request.user) if request else Bank.objects.none()

    class Meta:
        model = Inflow
        fields = ['id', 'title', 'bank', 'value']
        read_only_fields = ['user']
