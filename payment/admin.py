from django.contrib import admin
from . import models


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'card', 'description', 'category', 'date_payment', 'value')
    search_fields = ('name', 'user__username', 'user__email')


class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'bank', 'credit_limit', 'active')
    search_fields = ('name', 'user__username', 'user__email', 'bank__name')
    list_filter = ('active', 'bank')


admin.site.register(models.CreditCard, CreditCardAdmin)
admin.site.register(models.Payment, PaymentAdmin)
