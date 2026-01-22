from django.contrib import admin
from . import models


class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'agency', 'account')
    search_fields = ('name',)


admin.site.register(models.Bank, BankAdmin)
