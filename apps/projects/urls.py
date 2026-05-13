from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('create/', views.project_create, name='project_create'),
]
