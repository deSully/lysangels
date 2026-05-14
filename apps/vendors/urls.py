from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='vendor_list'),
    path('devenir-prestataire/', views.vendor_signup, name='vendor_signup'),
    path('<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('<int:pk>/contact/', views.reveal_contact, name='reveal_contact'),
]
