from django import forms
from .models import Signature


class SignatureForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = ['name', 'description', 'value', 'billing_day', 'is_active', 'bank', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
            'billing_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bank': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
            'value': 'Valor',
            'billing_day': 'Dia de Cobrança',
            'is_active': 'Ativa',
            'bank': 'Banco',
            'category': 'Categoria',
        }
