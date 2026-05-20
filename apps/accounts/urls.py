from django.urls import path
from . import views, admin_views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Admin Dashboard
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),

    # Gestion des pays
    path('admin/countries/', admin_views.country_list, name='admin_country_list'),
    path('admin/countries/create/', admin_views.country_create, name='admin_country_create'),
    path('admin/countries/<int:pk>/edit/', admin_views.country_edit, name='admin_country_edit'),
    path('admin/countries/<int:pk>/delete/', admin_views.country_delete, name='admin_country_delete'),

    # Gestion des villes
    path('admin/cities/', admin_views.city_list, name='admin_city_list'),
    path('admin/cities/create/', admin_views.city_create, name='admin_city_create'),
    path('admin/cities/<int:pk>/edit/', admin_views.city_edit, name='admin_city_edit'),
    path('admin/cities/<int:pk>/delete/', admin_views.city_delete, name='admin_city_delete'),

    # Gestion des types de services
    path('admin/service-types/', admin_views.service_type_list, name='admin_service_type_list'),
    path('admin/service-types/create/', admin_views.service_type_create, name='admin_service_type_create'),
    path('admin/service-types/<int:pk>/edit/', admin_views.service_type_edit, name='admin_service_type_edit'),
    path('admin/service-types/<int:pk>/delete/', admin_views.service_type_delete, name='admin_service_type_delete'),

    # Gestion des types d'événements
    path('admin/event-types/', admin_views.event_type_list, name='admin_event_type_list'),
    path('admin/event-types/create/', admin_views.event_type_create, name='admin_event_type_create'),
    path('admin/event-types/<int:pk>/edit/', admin_views.event_type_edit, name='admin_event_type_edit'),
    path('admin/event-types/<int:pk>/delete/', admin_views.event_type_delete, name='admin_event_type_delete'),

    # Gestion des demandes clients
    path('admin/projects/', admin_views.project_list, name='admin_project_list'),
    path('admin/projects/<int:pk>/', admin_views.project_detail, name='admin_project_detail'),
    path('admin/projects/<int:pk>/status/', admin_views.project_update_status, name='admin_project_update_status'),
    path('admin/projects/<int:pk>/notes/', admin_views.project_add_note, name='admin_project_add_note'),
    path('admin/projects/<int:pk>/delete/', admin_views.project_delete, name='admin_project_delete'),

    # Gestion des candidatures prestataires
    path('admin/applications/', admin_views.application_list, name='admin_application_list'),
    path('admin/applications/<int:pk>/', admin_views.application_detail, name='admin_application_detail'),
    path('admin/applications/<int:pk>/create-profile/', admin_views.application_create_profile, name='admin_application_create_profile'),
    path('admin/applications/<int:pk>/edit/', admin_views.application_edit, name='admin_application_edit'),
    path('admin/applications/<int:pk>/delete-image/<int:n>/', admin_views.application_delete_image, name='admin_application_delete_image'),
    path('admin/applications/<int:pk>/add-image/', admin_views.application_add_image, name='admin_application_add_image'),
    path('admin/applications/<int:pk>/resize-images/', admin_views.application_resize_images, name='admin_application_resize_images'),
    path('admin/applications/<int:pk>/delete/', admin_views.application_delete, name='admin_application_delete'),

    # Messages de contact
    path('admin/contact-messages/', admin_views.contact_message_list, name='admin_contact_message_list'),
    path('admin/contact-messages/<int:pk>/', admin_views.contact_message_detail, name='admin_contact_message_detail'),

    # Gestion des prestataires
    path('admin/vendors/', admin_views.vendor_list, name='admin_vendor_list'),
    path('admin/vendors/create/', admin_views.vendor_create, name='admin_vendor_create'),
    path('admin/vendors/<int:pk>/', admin_views.vendor_detail, name='admin_vendor_detail'),
    path('admin/vendors/<int:pk>/edit/', admin_views.vendor_edit, name='admin_vendor_edit'),
    path('admin/vendors/<int:pk>/toggle-active/', admin_views.vendor_toggle_active, name='admin_vendor_toggle_active'),
    path('admin/vendors/<int:vendor_id>/delete-image/<int:image_id>/', admin_views.vendor_delete_image, name='admin_vendor_delete_image'),
    path('admin/vendors/<int:vendor_id>/add-image/', admin_views.vendor_add_image, name='admin_vendor_add_image'),
    path('admin/vendors/<int:vendor_id>/set-cover-image/<int:image_id>/', admin_views.vendor_set_cover_image, name='admin_vendor_set_cover_image'),

    # Journal d'erreurs
    path('admin/errors/', admin_views.error_log_list, name='admin_error_log_list'),
    path('admin/errors/<int:pk>/', admin_views.error_log_detail, name='admin_error_log_detail'),

    # Publicités
    path('admin/ads/', admin_views.ad_list, name='admin_ad_list'),
    path('admin/ads/create/', admin_views.ad_create, name='admin_ad_create'),
    path('admin/ads/<int:pk>/edit/', admin_views.ad_edit, name='admin_ad_edit'),
    path('admin/ads/<int:pk>/delete/', admin_views.ad_delete, name='admin_ad_delete'),

    # Paramètres du site
    path('admin/settings/', admin_views.site_settings, name='admin_site_settings'),
]
