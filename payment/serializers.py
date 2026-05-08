from categories.models import Category
from rest_framework import serializers
from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['category'].queryset = Category.objects.filter(user=request.user) if request else Category.objects.none()

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['user']
