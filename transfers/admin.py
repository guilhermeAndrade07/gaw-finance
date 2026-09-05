from django.contrib import admin

from .models import BankTransfer


@admin.register(BankTransfer)
class BankTransferAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'source_bank', 'destination_bank', 'value', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = (
        'user',
        'title',
        'source_bank',
        'destination_bank',
        'value',
        'created_at',
        'update_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
