from django import forms
from banks.models import Bank
from . import models


class InflowForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank'].queryset = Bank.objects.filter(user=user) if user else Bank.objects.none()

    class Meta:
        model = models.Inflow
        fields = ['title', 'bank', 'value']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'bank': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Título',
            'bank': 'Banco',
            'value': 'Valor',
        }
