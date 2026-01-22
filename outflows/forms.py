from django import forms
from django.core.exceptions import ValidationError
from . import models


class OutflowForm(forms.ModelForm):

    class Meta:
        model = models.Outflow
        fields = ['title', 'bank', 'category', 'value']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'bank': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Título',
            'bank': 'Banco',
            'category': 'Categoria',
            'value': 'Valor',
        }

    def clean_value(self):
        value = self.cleaned_data.get('value')
        bank = self.cleaned_data.get('bank')

        if bank and value and value > bank.balance:
            raise ValidationError(
                f'Saldo insuficiente! Balance disponível: R$ {bank.balance}'
            )
        return value
