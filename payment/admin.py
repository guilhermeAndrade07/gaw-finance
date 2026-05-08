from django.contrib import admin
from . import models


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'description', 'category', 'date_payment', 'value')
    search_fields = ('name', 'user__username', 'user__email')


admin.site.register(models.Payment, PaymentAdmin)
