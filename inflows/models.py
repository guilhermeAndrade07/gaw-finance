from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from banks.models import Bank


class Inflow(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inflows', null=True, blank=True)

    title = models.CharField(max_length=100, null=True, blank=True)
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='inflows')
    value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(value__gt=0),
                name='inflow_value_positive',
            ),
        ]

    def __str__(self):
        return str(self.bank)
