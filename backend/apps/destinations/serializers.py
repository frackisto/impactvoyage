from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accommodations.serializers import HotelCardSerializer, ResidenceCardSerializer
from apps.activities.serializers import ActivityCardSerializer
from apps.core.serializers import (
    GalleryImageSerializer,
    LinesField,
    RatingSummarySerializer,
    TagSerializer,
)
from apps.reviews.selectors import rating_summary
from apps.tours.serializers import TourCardSerializer

from .models import Destination
from .references import DestinationMiniSerializer  # noqa: F401 (réexport)


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
    """
    Page immersive (CdC § 8) : galerie, attractions, conseils, offres liées
    publiées (circuits, hôtels, résidences, activités) et note des avis.
    """

    images = GalleryImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    attractions = LinesField()
    tours = TourCardSerializer(many=True, read_only=True)
    hotels = HotelCardSerializer(many=True, read_only=True)
    residences = ResidenceCardSerializer(many=True, read_only=True)
    activities = ActivityCardSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "slug", "name", "continent", "country_code", "city",
            "short_description", "description", "best_period", "attractions", "tips",
            "cover_image", "cover_alt", "images", "tags", "tours", "hotels", "residences",
            "activities", "rating",
        ]

    @extend_schema_field(RatingSummarySerializer)
    def get_rating(self, obj):
        return rating_summary(destination=obj)
