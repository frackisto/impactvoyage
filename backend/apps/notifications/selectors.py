from .models import Notification


def notifications_for(user, unread_only=False):
    qs = Notification.objects.filter(recipient=user).select_related("content_type")
    return qs.filter(is_read=False) if unread_only else qs


def unread_count(user):
    return Notification.objects.filter(recipient=user, is_read=False).count()
