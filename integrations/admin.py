from django.contrib import admin

from integrations.models import WhatsAppBinding, WhatsAppMessageLog


@admin.register(WhatsAppBinding)
class WhatsAppBindingAdmin(admin.ModelAdmin):
    list_display = ['phone', 'user', 'instance_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'instance_name']
    search_fields = ['phone', 'user__username']
    readonly_fields = ['created_at', 'update_at']


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    list_display = ['phone', 'direction', 'interpreted_intent', 'result_status', 'created_at']
    list_filter = ['direction', 'result_status', 'interpreted_intent']
    search_fields = ['phone', 'message_text']
    readonly_fields = [
        'binding', 'message_id', 'direction', 'phone', 'raw_body',
        'message_text', 'interpreted_intent', 'result_status',
        'response_text', 'created_at', 'update_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
