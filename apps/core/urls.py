from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    
    # Pages légales
    path('terms/', views.terms_of_service, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('legal/', views.legal_notice, name='legal'),
    
    # PWA
    path('offline/', views.offline, name='offline'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # API
    path('api/quartiers/', views.get_quartiers_by_city, name='api_quartiers'),
]
