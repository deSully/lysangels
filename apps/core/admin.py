from django.contrib import admin
from .models import Country, City, Quartier


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'flag_emoji', 'is_active', 'display_order', 'city_count']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']

    def city_count(self, obj):
        return obj.cities.count()
    city_count.short_description = 'Nombre de villes'


class QuartierInline(admin.TabularInline):
    model = Quartier
    extra = 1
    fields = ['name', 'is_active']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'is_active', 'quartier_count', 'created_at']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'country__name']
    list_select_related = ['country']
    inlines = [QuartierInline]

    def quartier_count(self, obj):
        return obj.quartiers.count()
    quartier_count.short_description = 'Nombre de quartiers'


@admin.register(Quartier)
class QuartierAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city__country', 'city', 'created_at']
    search_fields = ['name', 'city__name', 'city__country__name']
    list_select_related = ['city', 'city__country']
