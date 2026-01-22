from django.contrib import admin
from . import models


class InflowAdmin(admin.ModelAdmin):
    list_display = ('title', 'bank', 'value')
    search_fields = ('title',)


admin.site.register(models.Inflow, InflowAdmin)
