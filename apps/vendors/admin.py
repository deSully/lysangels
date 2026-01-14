from django.contrib import admin
from .models import ServiceType, VendorProfile, VendorImage, Review


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


class VendorImageInline(admin.TabularInline):
    model = VendorImage
    extra = 1


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'city', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'city']
    search_fields = ['business_name', 'user__username', 'user__email']
    filter_horizontal = ['service_types']
    inlines = [VendorImageInline]


@admin.register(VendorImage)
class VendorImageAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'is_cover', 'caption', 'created_at']
    list_filter = ['is_cover', 'created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'client', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['vendor__business_name', 'client__username']
