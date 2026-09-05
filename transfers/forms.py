from django import forms
from django.core.exceptions import ValidationError

from banks.models import Bank

from . import models


class BankTransferForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        banks = Bank.objects.filter(user=user) if user else Bank.objects.none()
        self.fields['source_bank'].queryset = banks
        self.fields['destination_bank'].queryset = banks

    class Meta:
        model = models.BankTransfer
        fields = ['title', 'source_bank', 'destination_bank', 'value']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'source_bank': forms.Select(attrs={'class': 'form-control'}),
            'destination_bank': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'title': 'Título',
            'source_bank': 'Banco de origem',
            'destination_bank': 'Banco de destino',
            'value': 'Valor',
        }

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_bank')
        destination = cleaned_data.get('destination_bank')
        if source and destination and source.pk == destination.pk:
            raise ValidationError('O banco de origem e o banco de destino devem ser diferentes.')
        return cleaned_data

    def clean_value(self):
        value = self.cleaned_data.get('value')
        source = self.cleaned_data.get('source_bank')
        if source and value and value > source.current_balance:
            raise ValidationError(
                f'Saldo insuficiente! Saldo disponivel: R$ {source.current_balance}'
            )
        return value
