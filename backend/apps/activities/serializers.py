from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.serializers import (
    CategorySerializer,
    GalleryImageSerializer,
    MoneyField,
    MoneySerializer,
    money_repr,
)
from apps.destinations.references import DestinationMiniSerializer
from apps.offers.selectors import promo_price_for

from .models import Activity


class ActivityCardSerializer(serializers.ModelSerializer):
    price = MoneyField(amount="base_price")

    class Meta:
        model = Activity
        fields = [
            "id", "slug", "title", "short_description", "cover_image", "cover_alt",
            "duration_hours", "price",
        ]


class ActivityListSerializer(ActivityCardSerializer):
    # Présent seulement quand la liste est filtrée par date (activities.selectors).
    places_left = serializers.IntegerField(read_only=True, default=None, allow_null=True)
    destination = DestinationMiniSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta(ActivityCardSerializer.Meta):
        fields = ActivityCardSerializer.Meta.fields + [
            "destination", "category", "max_participants", "booking_mode", "is_featured",
            "places_left",
        ]


class ActivityDetailSerializer(ActivityListSerializer):
    places_left = None  # uniquement dans les listes filtrées par date
    images = GalleryImageSerializer(many=True, read_only=True)
    promo_price = serializers.SerializerMethodField()

    class Meta(ActivityListSerializer.Meta):
        fields = [f for f in ActivityListSerializer.Meta.fields if f != "places_left"] + [
            "description", "images", "promo_price",
        ]

    @extend_schema_field(MoneySerializer(allow_null=True))
    def get_promo_price(self, obj):
        return money_repr(promo_price_for(obj), obj.currency, self.context.get("request"))
