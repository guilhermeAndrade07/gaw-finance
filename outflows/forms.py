from banks.models import Bank
from categories.models import Category
from django import forms
from django.core.exceptions import ValidationError
from . import models


class OutflowForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank'].queryset = Bank.objects.filter(user=user) if user else Bank.objects.none()
        self.fields['category'].queryset = Category.objects.filter(user=user) if user else Category.objects.none()

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

        if bank and value and value > bank.current_balance:
            raise ValidationError(
                f'Saldo insuficiente! Saldo disponível: R$ {bank.current_balance}'
            )
        return value
