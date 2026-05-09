from datetime import date

from django import forms

from banks.models import Bank

from .models import InvestmentAsset, InvestmentMovement


class InvestmentAssetForm(forms.ModelForm):
    initial_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=20,
        label='Valor inicial aplicado',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    initial_date = forms.DateField(
        required=False,
        initial=date.today,
        label='Data do aporte inicial',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    register_cash_flow = forms.BooleanField(
        required=False,
        initial=True,
        label='Registrar tambem no fluxo de caixa',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank'].queryset = Bank.objects.filter(user=user) if user else Bank.objects.none()
        self.fields['current_value'].required = False

    class Meta:
        model = InvestmentAsset
        fields = [
            'name',
            'asset_type',
            'subtype',
            'institution',
            'bank',
            'maturity_date',
            'expected_rate',
            'liquidity_type',
            'current_value',
            'notes',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_type': forms.Select(attrs={'class': 'form-control'}),
            'subtype': forms.TextInput(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'bank': forms.Select(attrs={'class': 'form-control'}),
            'maturity_date': forms.DateInput(attrs={'class': 'form-control fixed-income-field', 'type': 'date'}),
            'expected_rate': forms.TextInput(attrs={'class': 'form-control fixed-income-field'}),
            'liquidity_type': forms.Select(attrs={'class': 'form-control fixed-income-field'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nome do ativo',
            'asset_type': 'Tipo',
            'subtype': 'Subtipo',
            'institution': 'Instituicao',
            'bank': 'Banco de origem',
            'maturity_date': 'Data de vencimento',
            'expected_rate': 'Taxa esperada',
            'liquidity_type': 'Liquidez',
            'current_value': 'Valor atual',
            'notes': 'Observacoes',
            'is_active': 'Ativo',
        }

    def clean(self):
        cleaned_data = super().clean()
        current_value = cleaned_data.get('current_value')
        initial_amount = cleaned_data.get('initial_amount')
        initial_date = cleaned_data.get('initial_date')

        if current_value is None:
            cleaned_data['current_value'] = initial_amount or 0

        if initial_amount and not initial_date:
            cleaned_data['initial_date'] = date.today()

        return cleaned_data


class InvestmentMovementForm(forms.ModelForm):
    def __init__(self, *args, user=None, initial_asset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = InvestmentAsset.objects.filter(user=user, is_active=True) if user else InvestmentAsset.objects.none()
        if initial_asset:
            self.fields['asset'].initial = initial_asset
        self.fields['movement_date'].initial = date.today()

    class Meta:
        model = InvestmentMovement
        fields = ['asset', 'operation_type', 'value', 'movement_date', 'register_cash_flow', 'notes']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-control'}),
            'operation_type': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'movement_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'register_cash_flow': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'asset': 'Ativo',
            'operation_type': 'Operacao',
            'value': 'Valor',
            'movement_date': 'Data',
            'register_cash_flow': 'Registrar tambem no fluxo de caixa',
            'notes': 'Observacoes',
        }

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get('asset')
        operation_type = cleaned_data.get('operation_type')
        value = cleaned_data.get('value')

        if asset and operation_type == InvestmentMovement.REDEMPTION and value and value > asset.current_value:
            self.add_error('value', 'O resgate nao pode ser maior que o valor atual do ativo.')

        return cleaned_data
