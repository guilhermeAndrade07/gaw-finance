import re
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Sum

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
    closing_day = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    due_day = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.bank.name}'


class Invoice(models.Model):
    OPEN = 'open'
    CLOSED = 'closed'
    PAID = 'paid'
    STATUS_CHOICES = [
        (OPEN, 'Aberta'),
        (CLOSED, 'Fechada'),
        (PAID, 'Paga'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='invoices')
    closing_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-closing_date']
        constraints = [
            models.UniqueConstraint(
                fields=['card', 'closing_date'],
                name='uniq_invoice_per_cycle',
            )
        ]

    @property
    def total(self):
        result = self.payments.aggregate(total=Sum('value'))['total']
        return result or Decimal('0.00')

    def __str__(self):
        return f'{self.card.name} - Fech. {self.closing_date} - Venc. {self.due_date}'


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
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
    )
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
