from django import forms
from . import models


class PaymentForm(forms.ModelForm):

    parcelas = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        label='Parcelas',
    )

    class Meta:
        model = models.Payment
        fields = ['name', 'description', 'category', 'date_payment', 'value', 'parcelas']
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
