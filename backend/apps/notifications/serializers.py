from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    event_label = serializers.CharField(source="get_event_display", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "event", "event_label", "title", "message", "link", "is_read",
                  "read_at", "created_at"]
