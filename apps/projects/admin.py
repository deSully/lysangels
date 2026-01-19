from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import EventType, Project, AdminRecommendation


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


class AdminRecommendationInline(admin.TabularInline):
    """Inline pour ajouter des recommandations directement depuis la page projet"""
    model = AdminRecommendation
    extra = 1
    fields = ['vendor', 'admin_note', 'status', 'created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['vendor']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendor', 'recommended_by')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'client_link', 'event_type', 'event_date', 'city',
        'budget_display', 'services_display', 'status', 'recommendations_count', 'created_at'
    ]
    list_filter = ['status', 'event_type', 'city', 'created_at']
    search_fields = ['title', 'client__username', 'client__email', 'description']
    filter_horizontal = ['services_needed']
    date_hierarchy = 'event_date'
    inlines = [AdminRecommendationInline]

    fieldsets = (
        ('Informations du projet', {
            'fields': ('title', 'client', 'event_type', 'description', 'status')
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

    def client_link(self, obj):
        """Lien vers le client"""
        url = reverse('admin:accounts_user_changelist') + f'?id={obj.client.id}'
        return format_html('<a href="{}">{}</a>', url, obj.client.get_full_name() or obj.client.email)
    client_link.short_description = 'Client'
    client_link.admin_order_field = 'client__first_name'

    def budget_display(self, obj):
        """Affiche le budget formaté"""
        if obj.budget_max:
            return f"{int(obj.budget_min):,} - {int(obj.budget_max):,} FCFA"
        return f"{int(obj.budget_min):,} FCFA"
    budget_display.short_description = 'Budget'

    def services_display(self, obj):
        """Affiche les services recherchés"""
        services = obj.services_needed.all()[:3]
        names = [s.name for s in services]
        if obj.services_needed.count() > 3:
            names.append(f'+{obj.services_needed.count() - 3}')
        return ', '.join(names) or '-'
    services_display.short_description = 'Services'

    def recommendations_count(self, obj):
        """Nombre de recommandations pour ce projet"""
        count = obj.recommendations.count()
        if count == 0:
            return format_html('<span style="color: #999;">0</span>')
        return format_html(
            '<span style="color: #8b5cf6; font-weight: bold;">{}</span>',
            count
        )
    recommendations_count.short_description = 'Reco.'


@admin.register(AdminRecommendation)
class AdminRecommendationAdmin(admin.ModelAdmin):
    """Admin dédié pour gérer les recommandations Suzy"""
    list_display = [
        'project_link', 'vendor_link', 'status_badge', 'admin_note_preview',
        'recommended_by', 'created_at', 'sent_at'
    ]
    list_filter = ['status', 'created_at', 'recommended_by']
    search_fields = [
        'project__title', 'vendor__business_name',
        'project__client__email', 'admin_note'
    ]
    autocomplete_fields = ['project', 'vendor']
    readonly_fields = ['created_at', 'sent_at', 'viewed_at']

    fieldsets = (
        ('Recommandation', {
            'fields': ('project', 'vendor', 'admin_note')
        }),
        ('Statut', {
            'fields': ('status', 'recommended_by')
        }),
        ('Historique', {
            'fields': ('created_at', 'sent_at', 'viewed_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['send_recommendations', 'mark_as_pending']

    def project_link(self, obj):
        """Lien vers le projet"""
        url = reverse('admin:projects_project_change', args=[obj.project.id])
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            url,
            obj.project.description[:100] + '...' if len(obj.project.description) > 100 else obj.project.description,
            obj.project.title[:30] + '...' if len(obj.project.title) > 30 else obj.project.title
        )
    project_link.short_description = 'Projet'
    project_link.admin_order_field = 'project__title'

    def vendor_link(self, obj):
        """Lien vers le prestataire"""
        url = reverse('admin:vendors_vendorprofile_change', args=[obj.vendor.id])
        return format_html('<a href="{}">{}</a>', url, obj.vendor.business_name)
    vendor_link.short_description = 'Prestataire'
    vendor_link.admin_order_field = 'vendor__business_name'

    def status_badge(self, obj):
        """Badge coloré pour le statut"""
        colors = {
            'pending': '#f59e0b',    # Orange
            'sent': '#3b82f6',       # Bleu
            'viewed': '#8b5cf6',     # Violet
            'contacted': '#10b981',  # Vert
            'accepted': '#059669',   # Vert foncé
            'declined': '#ef4444',   # Rouge
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'status'

    def admin_note_preview(self, obj):
        """Aperçu de la note"""
        if len(obj.admin_note) > 50:
            return obj.admin_note[:50] + '...'
        return obj.admin_note
    admin_note_preview.short_description = 'Note Suzy'

    def save_model(self, request, obj, form, change):
        """Enregistre l'admin qui a fait la recommandation"""
        if not change:  # Nouvelle recommandation
            obj.recommended_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description='Envoyer les recommandations sélectionnées aux clients')
    def send_recommendations(self, request, queryset):
        """Action pour envoyer les recommandations en attente"""
        updated = 0
        for reco in queryset.filter(status='pending'):
            reco.status = 'sent'
            reco.sent_at = timezone.now()
            reco.save()
            # Le signal va envoyer la notification
            updated += 1
        self.message_user(request, f'{updated} recommandation(s) envoyée(s).')

    @admin.action(description='Remettre en attente')
    def mark_as_pending(self, request, queryset):
        """Remet les recommandations en attente"""
        updated = queryset.update(status='pending', sent_at=None)
        self.message_user(request, f'{updated} recommandation(s) remise(s) en attente.')
