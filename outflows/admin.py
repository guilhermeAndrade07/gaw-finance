from django.contrib import admin
from . import models


class OutflowAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'bank', 'category', 'value')
    search_fields = ('title', 'user__username', 'user__email')


admin.site.register(models.Outflow, OutflowAdmin)
