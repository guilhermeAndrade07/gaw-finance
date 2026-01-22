from django.db import models


class Bank(models.Model):

    name = models.CharField(max_length=150)
    account_type = models.TextField(max_length=200)
    agency = models.IntegerField()
    account = models.IntegerField()
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
