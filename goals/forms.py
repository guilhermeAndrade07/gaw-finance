from categories.models import Category
from django import forms
from django.core.exceptions import ValidationError

from . import models


class MonthlyGoalForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        else:
            self.fields['category'].queryset = Category.objects.none()

    class Meta:
        model = models.MonthlyGoal
        fields = ['category', 'value', 'month', 'year']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'month': forms.Select(attrs={'class': 'form-control'}, choices=[(i, models.MONTHS_PT_BR[i]) for i in range(1, 13)]),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2100'}),
        }
        labels = {
            'category': 'Categoria',
            'value': 'Valor da Meta (R$)',
            'month': 'Mes',
            'year': 'Ano',
        }

    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value is not None and value <= 0:
            raise ValidationError('O valor da meta deve ser maior que zero.')
        return value

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        month = cleaned_data.get('month')
        year = cleaned_data.get('year')

        if month and year and self.user:
            qs = models.MonthlyGoal.objects.filter(
                user=self.user, category=category, month=month, year=year,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                label = category.name if category else 'Sem categoria'
                raise ValidationError(
                    f'Ja existe uma meta para "{label}" em {models.MONTHS_PT_BR.get(month, month)}/{year}.'
                )
        return cleaned_data
