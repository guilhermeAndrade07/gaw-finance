from django.contrib import admin
from .models import Signature


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'value', 'billing_day', 'is_active', 'credit_card', 'category')
    list_filter = ('is_active', 'credit_card', 'category')
    search_fields = ('name', 'description', 'user__username', 'user__email')
