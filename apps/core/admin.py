from django.contrib import admin
from .models import Country, City


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'flag_emoji', 'is_active', 'display_order', 'city_count']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']

    def city_count(self, obj):
        return obj.cities.count()
    city_count.short_description = 'Nombre de villes'


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'is_active', 'created_at']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'country__name']
    list_select_related = ['country']
