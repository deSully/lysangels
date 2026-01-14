from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_staff']
    list_filter = ['user_type', 'is_verified', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations LysAngels', {
            'fields': ('user_type', 'phone', 'city', 'profile_image', 'is_verified')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations LysAngels', {
            'fields': ('user_type', 'phone', 'city')
        }),
    )
