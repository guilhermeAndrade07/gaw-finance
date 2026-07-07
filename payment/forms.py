from banks.models import Bank
from categories.models import Category
from datetime import datetime
from django import forms
from django.db.models import Q
from . import models


class CreditCardForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank'].queryset = Bank.objects.filter(user=user) if user else Bank.objects.none()

    class Meta:
        model = models.CreditCard
        fields = ['name', 'bank', 'credit_limit', 'closing_day', 'due_day', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank': forms.Select(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'closing_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nome do cartão',
            'bank': 'Banco',
            'credit_limit': 'Limite',
            'closing_day': 'Dia de Fechamento',
            'due_day': 'Dia de Vencimento',
            'active': 'Ativo',
        }


class PaymentForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user) if user else Category.objects.none()
        if user:
            card_queryset = models.CreditCard.objects.filter(user=user).filter(
                Q(active=True) | Q(id=getattr(self.instance, 'card_id', None))
            )
        else:
            card_queryset = models.CreditCard.objects.none()
        self.fields['card'].queryset = card_queryset
        self.fields['card'].required = True
        self.fields['card'].empty_label = 'Selecione um cartão'

        if self.instance and self.instance.pk and self.instance.date_payment:
            self.fields['date_payment'].initial = self.instance.date_payment.strftime('%d/%m/%Y')

    parcelas = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        label='Parcelas',
    )

    date_payment = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control js-date-mask',
            'placeholder': 'dd/mm/aaaa',
            'maxlength': 10,
        }),
        label='Data da Compra',
    )

    class Meta:
        model = models.Payment
        fields = ['card', 'name', 'category', 'date_payment', 'value', 'parcelas']
        widgets = {
            'card': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'card': 'Cartão',
            'name': 'Compra',
            'category': 'Categoria',
            'value': 'Valor',
        }

    def clean_date_payment(self):
        value = self.cleaned_data.get('date_payment')
        if not value:
            return None
        if isinstance(value, str):
            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise forms.ValidationError('Informe a data no formato dd/mm/aaaa.')
        return value
