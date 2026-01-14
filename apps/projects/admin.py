from django.contrib import admin
from .models import EventType, Project


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'event_type', 'event_date', 'city', 'status', 'created_at']
    list_filter = ['status', 'event_type', 'city', 'created_at']
    search_fields = ['title', 'client__username', 'client__email', 'description']
    filter_horizontal = ['services_needed']
    date_hierarchy = 'event_date'
