from banks.models import Bank
from categories.models import Category
from django import forms
from django.db.models import Q
from . import models


class CreditCardForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank'].queryset = Bank.objects.filter(user=user) if user else Bank.objects.none()

    class Meta:
        model = models.CreditCard
        fields = ['name', 'bank', 'credit_limit', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank': forms.Select(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nome do cartao',
            'bank': 'Banco',
            'credit_limit': 'Limite',
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
        self.fields['card'].empty_label = 'Selecione um cartao'

    parcelas = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        label='Parcelas',
    )

    class Meta:
        model = models.Payment
        fields = ['card', 'name', 'description', 'category', 'date_payment', 'value', 'parcelas']
        widgets = {
            'card': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date_payment': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'card': 'Cartao',
            'name': 'Compra',
            'description': 'Descricao',
            'category': 'Categoria',
            'date_payment': 'Data de vencimento',
            'value': 'Valor',
        }
