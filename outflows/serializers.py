from banks.models import Bank
from categories.models import Category
from rest_framework import serializers
from outflows.models import Outflow


class OutflowSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            self.fields['bank'].queryset = Bank.objects.filter(user=request.user)
            self.fields['category'].queryset = Category.objects.filter(user=request.user)
        else:
            self.fields['bank'].queryset = Bank.objects.none()
            self.fields['category'].queryset = Category.objects.none()

    class Meta:
        model = Outflow
        fields = ['id', 'title', 'bank', 'category', 'value']
        read_only_fields = ['user']
