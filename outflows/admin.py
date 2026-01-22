from django.contrib import admin
from . import models


class OutflowAdmin(admin.ModelAdmin):
    list_display = ('title', 'bank', 'category', 'value')
    search_fields = ('title',)


admin.site.register(models.Outflow, OutflowAdmin)
