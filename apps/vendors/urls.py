from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='vendor_list'),
    path('<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('portfolio/', views.portfolio_manage, name='portfolio_manage'),
    path('portfolio/upload/', views.portfolio_upload, name='portfolio_upload'),
    path('portfolio/delete/<int:image_id>/', views.portfolio_delete, name='portfolio_delete'),
    path('portfolio/set-cover/<int:image_id>/', views.portfolio_set_cover, name='portfolio_set_cover'),
    
    # Avis
    path('<int:vendor_id>/review/create/', views.create_review, name='create_review'),
    path('review/<int:review_id>/respond/', views.vendor_response_review, name='vendor_response_review'),
    path('review/<int:review_id>/moderate/', views.moderate_review, name='moderate_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
]
