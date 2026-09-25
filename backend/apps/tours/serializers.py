from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.activities.serializers import ActivityCardSerializer
from apps.core.serializers import (
    CategorySerializer,
    GalleryImageSerializer,
    LinesField,
    MoneyField,
    MoneySerializer,
    RatingSummarySerializer,
    money_repr,
)
from apps.destinations.references import DestinationMiniSerializer
from apps.offers.selectors import promo_price_for
from apps.reviews.selectors import rating_summary

from .models import Tour, TourDay, TourDeparture


class TourCardSerializer(serializers.ModelSerializer):
    price = MoneyField(amount="base_price")

    class Meta:
        model = Tour
        fields = [
            "id", "slug", "title", "short_description", "scope", "duration_days",
            "cover_image", "cover_alt", "price",
        ]


class TourListSerializer(TourCardSerializer):
    """Carte de résultat de recherche : annotations de tours.selectors.tour_list."""

    destination = DestinationMiniSerializer(read_only=True)
    theme = CategorySerializer(read_only=True)
    next_departure = serializers.DateField(read_only=True, default=None)
    rating_avg = serializers.FloatField(read_only=True, default=None)
    rating_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(TourCardSerializer.Meta):
        fields = TourCardSerializer.Meta.fields + [
            "destination", "theme", "is_custom", "is_featured", "next_departure",
            "rating_avg", "rating_count",
        ]


class TourDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TourDay
        fields = ["day_number", "title", "description"]


class TourDepartureSerializer(serializers.ModelSerializer):
    seats_left = serializers.IntegerField(read_only=True)
    price = MoneyField(amount="price", currency="tour.currency")

    class Meta:
        model = TourDeparture
        fields = ["id", "start_date", "end_date", "seats_left", "price", "status"]


class TourDetailSerializer(TourListSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)
    days = TourDaySerializer(many=True, read_only=True)
    departures = TourDepartureSerializer(many=True, read_only=True, source="open_departures")
    activities = ActivityCardSerializer(many=True, read_only=True)
    departure_points = LinesField()
    inclusions = LinesField()
    exclusions = LinesField()
    promo_price = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta(TourListSerializer.Meta):
        fields = [
            f for f in TourListSerializer.Meta.fields if f not in ("rating_avg", "rating_count")
        ] + [
            "description", "min_travelers", "max_travelers", "departure_points",
            "transport_info", "accommodation_info", "inclusions", "exclusions", "conditions",
            "booking_mode", "images", "days", "departures", "activities", "promo_price",
            "rating",
        ]

    @extend_schema_field(MoneySerializer(allow_null=True))
    def get_promo_price(self, obj):
        return money_repr(promo_price_for(obj), obj.currency, self.context.get("request"))

    @extend_schema_field(RatingSummarySerializer)
    def get_rating(self, obj):
        return rating_summary(tour=obj)
