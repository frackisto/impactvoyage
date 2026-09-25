from rest_framework import serializers

from apps.core.serializers import GalleryImageSerializer, LinesField, TagSerializer

from .models import Destination


class DestinationMiniSerializer(serializers.ModelSerializer):
    """Référence courte, imbriquée dans les circuits, hôtels, activités..."""

    class Meta:
        model = Destination
        fields = ["id", "slug", "name", "continent", "country_code", "city"]


class DestinationListSerializer(serializers.ModelSerializer):
    tours_count = serializers.IntegerField(read_only=True, default=0)
    hotels_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Destination
        fields = [
            "id", "slug", "name", "continent", "country_code", "city",
            "short_description", "cover_image", "cover_alt", "is_featured",
            "tours_count", "hotels_count",
        ]


class DestinationDetailSerializer(serializers.ModelSerializer):
    """Page immersive (CdC § 8) : galerie, attractions, conseils, offres liées."""

    images = GalleryImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    attractions = LinesField()
    tours = serializers.SerializerMethodField()
    hotels = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "slug", "name", "continent", "country_code", "city",
            "short_description", "description", "best_period", "attractions", "tips",
            "cover_image", "cover_alt", "images", "tags", "tours", "hotels", "activities",
        ]

    # Imports différés : ces apps importent elles-mêmes DestinationMiniSerializer.
    def get_tours(self, obj):
        from apps.tours.serializers import TourCardSerializer

        return TourCardSerializer(obj.tours.all(), many=True, context=self.context).data

    def get_hotels(self, obj):
        from apps.accommodations.serializers import HotelCardSerializer

        return HotelCardSerializer(obj.hotels.all(), many=True, context=self.context).data

    def get_activities(self, obj):
        from apps.activities.serializers import ActivityCardSerializer

        return ActivityCardSerializer(obj.activities.all(), many=True, context=self.context).data
