from django.contrib import admin
from .models import ServiceType, VendorProfile, VendorImage, ContactView


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


class VendorImageInline(admin.TabularInline):
    model = VendorImage
    extra = 1


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'city', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'city']
    search_fields = ['business_name']
    filter_horizontal = ['service_types', 'countries']
    inlines = [VendorImageInline]


@admin.register(VendorImage)
class VendorImageAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'is_cover', 'caption', 'created_at']
    list_filter = ['is_cover', 'created_at']


@admin.register(ContactView)
class ContactViewAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'ip_address', 'viewed_at', 'session_key']
    list_filter = ['vendor', 'viewed_at']
    search_fields = ['vendor__business_name', 'ip_address']
    readonly_fields = ['vendor', 'ip_address', 'user_agent', 'viewed_at', 'session_key']
    ordering = ['-viewed_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
