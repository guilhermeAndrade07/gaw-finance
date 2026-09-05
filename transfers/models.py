from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from banks.models import Bank


class BankTransfer(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bank_transfers',
    )
    title = models.CharField(max_length=100, null=True, blank=True)
    source_bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name='transfers_sent',
    )
    destination_bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name='transfers_received',
    )
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
                condition=~models.Q(source_bank=models.F('destination_bank')),
                name='bank_transfer_different_banks',
            ),
        ]

    def clean(self):
        if self.source_bank_id == self.destination_bank_id:
            raise ValidationError('O banco de origem e o banco de destino devem ser diferentes.')

        if self.user_id and self.source_bank_id and self.source_bank.user_id != self.user_id:
            raise ValidationError('O banco de origem nao pertence ao usuario autenticado.')

        if self.user_id and self.destination_bank_id and self.destination_bank.user_id != self.user_id:
            raise ValidationError('O banco de destino nao pertence ao usuario autenticado.')

    def __str__(self):
        return f'{self.source_bank} -> {self.destination_bank} - R$ {self.value}'
