from django.contrib import admin
from . import models


class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'account_type', 'agency', 'account', 'initial_balance', 'balance')
    search_fields = ('name', 'user__username', 'user__email')


admin.site.register(models.Bank, BankAdmin)
