from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='vendor_list'),
    path('devenir-prestataire/', views.vendor_pitch, name='vendor_pitch'),
    path('devenir-prestataire/candidature/', views.vendor_signup, name='vendor_signup'),
    path('<slug:slug>/', views.vendor_detail, name='vendor_detail'),
    path('<slug:slug>/contact/', views.reveal_contact, name='reveal_contact'),
    path('id/<int:pk>/', views.vendor_detail_by_pk, name='vendor_detail_by_pk'),
]
