from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'proposal_request', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username']
    date_hierarchy = 'created_at'
