def notifications_processor(request):
    """Context processor pour les notifications"""
    if request.user.is_authenticated:
        from apps.core.models import Notification
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return {
            'unread_notifications_count': unread_notifications
        }
    return {
        'unread_notifications_count': 0
    }
