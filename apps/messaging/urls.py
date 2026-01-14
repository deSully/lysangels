from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:request_id>/', views.start_conversation, name='start_conversation'),
]
