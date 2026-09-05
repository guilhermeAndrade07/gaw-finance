from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from banks.models import Bank

from .models import BankTransfer
from .services import create_bank_transfer


class BankTransferSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        banks = Bank.objects.filter(user=request.user) if request else Bank.objects.none()
        self.fields['source_bank'].queryset = banks
        self.fields['destination_bank'].queryset = banks

    def validate(self, attrs):
        if attrs['source_bank'].pk == attrs['destination_bank'].pk:
            raise serializers.ValidationError(
                'O banco de origem e o banco de destino devem ser diferentes.'
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = validated_data.pop('user', request.user)
        try:
            return create_bank_transfer(user=user, **validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'non_field_errors': exc.messages})

    class Meta:
        model = BankTransfer
        fields = [
            'id',
            'title',
            'source_bank',
            'destination_bank',
            'value',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
