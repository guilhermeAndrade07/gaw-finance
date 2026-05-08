from django.contrib.auth.models import User
from django.db import models
from banks.models import Bank
from categories.models import Category


class Outflow(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outflows', null=True, blank=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='outflows')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='outflows', null=True, blank=True)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.category)
