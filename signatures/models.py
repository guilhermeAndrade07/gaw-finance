from django.contrib.auth.models import User
from django.db import models
from banks.models import Bank
from categories.models import Category


class Signature(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signatures', null=True, blank=True)
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    billing_day = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='signatures')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='signatures', null=True, blank=True)

    last_generated_month = models.PositiveIntegerField(null=True, blank=True)
    last_generated_year = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
