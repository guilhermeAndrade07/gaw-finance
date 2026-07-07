from categories.models import Category
from django import forms
from payment.models import CreditCard
from .models import Signature


class SignatureForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['credit_card'].queryset = (
            CreditCard.objects.filter(user=user, active=True)
            if user else CreditCard.objects.none()
        )
        self.fields['credit_card'].required = True
        self.fields['credit_card'].empty_label = 'Selecione um cartão'
        self.fields['category'].queryset = Category.objects.filter(user=user) if user else Category.objects.none()

    class Meta:
        model = Signature
        fields = ['name', 'description', 'value', 'billing_day', 'is_active', 'credit_card', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
            'billing_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'credit_card': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
            'value': 'Valor',
            'billing_day': 'Dia de Cobrança',
            'is_active': 'Ativa',
            'credit_card': 'Cartão de Crédito',
            'category': 'Categoria',
        }
