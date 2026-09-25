from rest_framework import serializers

from apps.core.serializers import MediaAssetSerializer
from apps.destinations.serializers import DestinationMiniSerializer

from .models import Event


class EventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id", "slug", "title", "short_description", "category", "date", "end_date",
            "location", "cover_image", "cover_alt", "is_featured",
        ]


class EventDetailSerializer(EventListSerializer):
    destination = DestinationMiniSerializer(read_only=True)
    media = MediaAssetSerializer(many=True, read_only=True)
    albums = serializers.SlugRelatedField(slug_field="slug", many=True, read_only=True)

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + [
            "description", "destination", "participants_count", "partners", "media", "albums",
        ]
