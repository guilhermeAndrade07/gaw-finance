from django import forms
from . import models


class BankForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields.pop('initial_balance')

    class Meta:
        model = models.Bank
        fields = ['name', 'account_type', 'agency', 'account', 'initial_balance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'agency': forms.NumberInput(attrs={'class': 'form-control'}),
            'account': forms.NumberInput(attrs={'class': 'form-control'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'name': 'Nome',
            'account_type': 'Tipo de Conta',
            'agency': 'Agência',
            'account': 'Conta',
            'initial_balance': 'Saldo Inicial',
        }
