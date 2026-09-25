from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from categories.models import Category
from payment.models import CreditCard, Payment


class Signature(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signatures', null=True, blank=True)
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    billing_day = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    is_active = models.BooleanField(default=True)
    credit_card = models.ForeignKey(CreditCard, on_delete=models.PROTECT, related_name='signatures', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='signatures', null=True, blank=True)

    last_generated_month = models.PositiveIntegerField(null=True, blank=True)
    last_generated_year = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                condition=Q(value__gt=0),
                name='signature_value_positive',
            ),
            models.CheckConstraint(
                condition=Q(billing_day__gte=1, billing_day__lte=31),
                name='signature_billing_day_range',
            ),
        ]

    def __str__(self):
        return self.name


class SignatureCharge(models.Model):
    signature = models.ForeignKey(
        Signature,
        on_delete=models.CASCADE,
        related_name='charges',
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='signature_charge',
    )
    reference_month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    reference_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reference_year', '-reference_month', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['signature', 'reference_year', 'reference_month'],
                name='uniq_signature_charge_per_month',
            ),
            models.CheckConstraint(
                condition=Q(reference_month__gte=1, reference_month__lte=12),
                name='signature_charge_month_range',
            ),
            models.CheckConstraint(
                condition=Q(reference_year__gte=2000, reference_year__lte=2100),
                name='signature_charge_year_range',
            ),
        ]

    def __str__(self):
        return f'{self.signature.name} - {self.reference_month}/{self.reference_year}'
