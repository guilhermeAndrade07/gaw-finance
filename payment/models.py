from django.db import models
from categories.models import Category
import re


class Payment(models.Model):

    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='payment', null=True, blank=True)
    date_payment = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    parcelas = models.PositiveIntegerField(default=1)
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
