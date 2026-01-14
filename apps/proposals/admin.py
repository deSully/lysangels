from django.contrib import admin
from .models import ProposalRequest, Proposal


@admin.register(ProposalRequest)
class ProposalRequestAdmin(admin.ModelAdmin):
    list_display = ['project', 'vendor', 'status', 'created_at', 'viewed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['project__title', 'vendor__business_name']
    date_hierarchy = 'created_at'


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['title', 'vendor', 'project', 'price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'vendor__business_name', 'project__title']
    date_hierarchy = 'created_at'
