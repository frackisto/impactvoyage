from rest_framework import serializers

from apps.core.serializers import MediaAssetSerializer
from apps.destinations.references import DestinationMiniSerializer

from .models import Event


class EventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id", "slug", "title", "short_description", "category", "date", "end_date",
            "location", "cover_image", "cover_alt", "is_featured",
        ]


class PartnerSerializer(serializers.Serializer):
    """Partenaire d'un événement (champ JSON « partenaires » de l'admin)."""

    name = serializers.CharField()
    logo = serializers.URLField(required=False, allow_blank=True)
    url = serializers.URLField(required=False, allow_blank=True)


class EventDetailSerializer(EventListSerializer):
    partners = PartnerSerializer(many=True, read_only=True)
    destination = DestinationMiniSerializer(read_only=True)
    media = MediaAssetSerializer(many=True, read_only=True)
    albums = serializers.SlugRelatedField(slug_field="slug", many=True, read_only=True)

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + [
            "description", "destination", "participants_count", "partners", "media", "albums",
        ]
