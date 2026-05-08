from banks.models import Bank
from categories.models import Category
from rest_framework import serializers
from .models import Signature


class SignatureSerializer(serializers.ModelSerializer):
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
        model = Signature
        fields = '__all__'
        read_only_fields = ['user']
