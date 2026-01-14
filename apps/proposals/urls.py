from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('send-request/<int:vendor_id>/', views.send_request, name='send_request'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('create/<int:request_id>/', views.create_proposal, name='create_proposal'),
    path('<int:pk>/', views.proposal_detail, name='proposal_detail'),
    path('<int:pk>/accept/', views.accept_proposal, name='accept_proposal'),
    path('<int:pk>/reject/', views.reject_proposal, name='reject_proposal'),
]
