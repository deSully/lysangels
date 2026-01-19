from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, admin_views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Réinitialisation de mot de passe
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

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

    # Gestion des quartiers
    path('admin/quartiers/', admin_views.quartier_list, name='admin_quartier_list'),
    path('admin/quartiers/create/', admin_views.quartier_create, name='admin_quartier_create'),
    path('admin/quartiers/<int:pk>/edit/', admin_views.quartier_edit, name='admin_quartier_edit'),
    path('admin/quartiers/<int:pk>/delete/', admin_views.quartier_delete, name='admin_quartier_delete'),

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

    # Gestion des projets
    path('admin/projects/', admin_views.project_list, name='admin_project_list'),
    path('admin/projects/<int:pk>/', admin_views.project_detail, name='admin_project_detail'),

    # Gestion des prestataires
    path('admin/vendors/', admin_views.vendor_list, name='admin_vendor_list'),
    path('admin/vendors/create/', admin_views.vendor_create, name='admin_vendor_create'),
    path('admin/vendors/<int:pk>/', admin_views.vendor_detail, name='admin_vendor_detail'),
    path('admin/vendors/<int:pk>/edit/', admin_views.vendor_edit, name='admin_vendor_edit'),
    path('admin/vendors/<int:pk>/toggle-active/', admin_views.vendor_toggle_active, name='admin_vendor_toggle_active'),
    path('admin/vendors/<int:vendor_id>/delete-image/<int:image_id>/', admin_views.vendor_delete_image, name='admin_vendor_delete_image'),

    # Gestion des demandes et propositions
    path('admin/proposal-requests/', admin_views.proposal_request_list, name='admin_proposal_request_list'),
    path('admin/proposals/', admin_views.proposal_list, name='admin_proposal_list'),
    path('admin/projects/<int:project_id>/proposals/create/', admin_views.admin_proposal_create, name='admin_proposal_create'),

    # Système de Recommandations Suzy
    path('admin/suzy-recommendations/', admin_views.admin_recommendations_list, name='admin_suzy_recommendations_list'),

    # Gestion des messages de contact
    path('admin/contact-messages/', admin_views.contact_message_list, name='admin_contact_message_list'),
    path('admin/contact-messages/<int:pk>/', admin_views.contact_message_detail, name='admin_contact_message_detail'),
]
