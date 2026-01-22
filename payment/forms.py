from django import forms
from . import models


class PaymentForm(forms.ModelForm):

    class Meta:
        model = models.Payment
        fields = ['name', 'description', 'category', 'date_payment', 'value']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date_payment': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Título',
            'description': 'Descrição',
            'category': 'Categoria',
            'date_payment': 'Data de Pagamento',
            'value': 'Valor',
        }
