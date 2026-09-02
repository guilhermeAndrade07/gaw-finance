from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum


class Bank(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='banks', null=True, blank=True)
    name = models.CharField(max_length=150)
    account_type = models.TextField(max_length=200)
    agency = models.IntegerField()
    account = models.IntegerField()
    initial_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def current_balance(self):
        inflows = self.inflows.aggregate(total=Sum('value'))['total'] or Decimal('0')
        outflows = self.outflows.aggregate(total=Sum('value'))['total'] or Decimal('0')
        return self.initial_balance + inflows - outflows
