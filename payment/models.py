import re
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from banks.models import Bank
from categories.models import Category


class CreditCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_cards', null=True, blank=True)
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='credit_cards')
    name = models.CharField(max_length=150)
    credit_limit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.bank.name}'


class Payment(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    card = models.ForeignKey(
        CreditCard,
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='payment', null=True, blank=True)
    date_payment = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    parcelas = models.PositiveIntegerField(default=1)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    @property
    def parcelas_display(self):
        match = re.search(r'\((\d+\/\d+)\)$', self.name or '')
        if match:
            return match.group(1)
        return f'1/{self.parcelas}'

    def __str__(self):
        return self.name
