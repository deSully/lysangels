from django.contrib import admin
from .models import EventType, Project


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'contact_name', 'contact_email', 'event_type', 'event_date', 'city',
        'budget_display', 'services_display', 'status', 'created_at'
    ]
    list_filter = ['status', 'event_type', 'city', 'created_at']
    search_fields = ['title', 'contact_name', 'contact_email', 'description']
    filter_horizontal = ['services_needed']
    date_hierarchy = 'event_date'

    fieldsets = (
        ('Informations de contact', {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        ('Informations du projet', {
            'fields': ('title', 'event_type', 'description', 'status')
        }),
        ('Détails de l\'événement', {
            'fields': ('event_date', 'event_time', 'city', 'location', 'guest_count')
        }),
        ('Budget', {
            'fields': ('budget_min', 'budget_max')
        }),
        ('Services recherchés', {
            'fields': ('services_needed',)
        }),
    )

    def budget_display(self, obj):
        """Affiche le budget formaté"""
        if obj.budget_min and obj.budget_max:
            return f"{int(obj.budget_min):,} - {int(obj.budget_max):,} FCFA"
        elif obj.budget_min:
            return f"{int(obj.budget_min):,} FCFA"
        elif obj.budget_max:
            return f"Max {int(obj.budget_max):,} FCFA"
        return '-'
    budget_display.short_description = 'Budget'

    def services_display(self, obj):
        """Affiche les services recherchés"""
        services = obj.services_needed.all()[:3]
        names = [s.name for s in services]
        if obj.services_needed.count() > 3:
            names.append(f'+{obj.services_needed.count() - 3}')
        return ', '.join(names) or '-'
    services_display.short_description = 'Services'
