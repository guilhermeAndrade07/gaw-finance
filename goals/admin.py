from django.contrib import admin

from . import models


@admin.register(models.MonthlyGoal)
class MonthlyGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'category_display', 'value', 'month', 'year',)
    list_filter = ('month', 'year',)
    search_fields = ('user__username', 'user__email', 'category__name',)

    @admin.display(description='Categoria')
    def category_display(self, obj):
        return obj.category_display
