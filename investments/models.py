from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from banks.models import Bank


class InvestmentAsset(models.Model):
    FIXED_INCOME = 'RENDA_FIXA'
    VARIABLE_INCOME = 'RENDA_VARIAVEL'
    CRYPTO = 'CRIPTO'
    FUNDS = 'FUNDOS'

    ASSET_TYPE_CHOICES = [
        (FIXED_INCOME, 'Renda Fixa'),
        (VARIABLE_INCOME, 'Renda Variavel'),
        (CRYPTO, 'Cripto'),
        (FUNDS, 'Fundos'),
    ]

    DAILY_LIQUIDITY = 'DIARIA'
    AT_MATURITY = 'VENCIMENTO'
    CUSTOM_LIQUIDITY = 'PERSONALIZADA'

    LIQUIDITY_TYPE_CHOICES = [
        (DAILY_LIQUIDITY, 'Liquidez diaria'),
        (AT_MATURITY, 'Somente no vencimento'),
        (CUSTOM_LIQUIDITY, 'Liquidez personalizada'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_assets')
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='investment_assets')
    name = models.CharField(max_length=150)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    subtype = models.CharField(max_length=100, null=True, blank=True)
    institution = models.CharField(max_length=150, null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    expected_rate = models.CharField(max_length=100, null=True, blank=True)
    liquidity_type = models.CharField(max_length=20, choices=LIQUIDITY_TYPE_CHOICES, null=True, blank=True)
    current_value = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class InvestmentMovement(models.Model):
    APPORTION = 'APORTE'
    REDEMPTION = 'RESGATE'

    OPERATION_TYPE_CHOICES = [
        (APPORTION, 'Aporte'),
        (REDEMPTION, 'Resgate'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_movements')
    asset = models.ForeignKey(InvestmentAsset, on_delete=models.CASCADE, related_name='movements')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPE_CHOICES)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    movement_date = models.DateField()
    register_cash_flow = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-movement_date', '-created_at']

    def clean(self):
        if self.value is None or self.value <= Decimal('0.00'):
            raise ValidationError('O valor da movimentacao deve ser maior que zero.')

    def __str__(self):
        return f'{self.get_operation_type_display()} - {self.asset.name}'

# Create your models here.
