from django.contrib import admin
from . import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'description',)
    search_fields = ('name', 'user__username', 'user__email')


admin.site.register(models.Category, CategoryAdmin)
