from django.contrib import admin
from .models import Signature


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'billing_day', 'is_active', 'bank', 'category')
    list_filter = ('is_active', 'bank', 'category')
    search_fields = ('name', 'description')
