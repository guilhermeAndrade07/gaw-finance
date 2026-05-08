from django.contrib import admin
from . import models


class InflowAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'bank', 'value')
    search_fields = ('title', 'user__username', 'user__email')


admin.site.register(models.Inflow, InflowAdmin)
