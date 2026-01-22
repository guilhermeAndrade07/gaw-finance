from django.contrib import admin
from . import models


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'category', 'date_payment', 'value')
    search_fields = ('name',)


admin.site.register(models.Payment, PaymentAdmin)
