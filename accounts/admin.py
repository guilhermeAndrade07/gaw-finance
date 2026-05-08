from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import Account


class AccountInline(admin.StackedInline):
    model = Account
    can_delete = False
    extra = 0


class UserAdmin(DjangoUserAdmin):
    inlines = [AccountInline]
    list_display = ('username', 'email', 'is_staff', 'account_name')

    @staticmethod
    def account_name(obj):
        if hasattr(obj, 'account'):
            return obj.account.name
        return obj.username

    account_name.short_description = 'Nome'


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
