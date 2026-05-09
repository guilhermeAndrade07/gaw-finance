from django.contrib import admin

from .models import InvestmentAsset, InvestmentMovement


@admin.register(InvestmentAsset)
class InvestmentAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'asset_type', 'bank', 'current_value', 'is_active')
    search_fields = ('name', 'subtype', 'institution', 'user__username', 'user__email')
    list_filter = ('asset_type', 'is_active', 'bank')


@admin.register(InvestmentMovement)
class InvestmentMovementAdmin(admin.ModelAdmin):
    list_display = ('asset', 'user', 'operation_type', 'value', 'movement_date', 'register_cash_flow')
    search_fields = ('asset__name', 'notes', 'user__username', 'user__email')
    list_filter = ('operation_type', 'register_cash_flow', 'movement_date')
