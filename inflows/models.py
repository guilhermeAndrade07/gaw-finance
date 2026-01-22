from django.db import models
from banks.models import Bank


class Inflow(models.Model):

    title = models.CharField(max_length=100, null=True, blank=True)
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='inflows')
    value = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.bank)
