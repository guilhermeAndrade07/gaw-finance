from django.contrib import admin
from . import models


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'card', 'description', 'category', 'date_payment', 'value', 'invoice')
    search_fields = ('name', 'user__username', 'user__email')
    list_filter = ('paid', 'card')


class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'bank', 'credit_limit', 'closing_day', 'due_day', 'active')
    search_fields = ('name', 'user__username', 'user__email', 'bank__name')
    list_filter = ('active', 'bank')


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('card', 'closing_date', 'due_date', 'status')
    list_filter = ('status', 'card')
    search_fields = ('card__name',)


admin.site.register(models.CreditCard, CreditCardAdmin)
admin.site.register(models.Payment, PaymentAdmin)
admin.site.register(models.Invoice, InvoiceAdmin)
