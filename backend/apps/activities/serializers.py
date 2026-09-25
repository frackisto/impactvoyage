from rest_framework import serializers

from apps.core.serializers import (
    CategorySerializer,
    GalleryImageSerializer,
    MoneyField,
    money_repr,
)
from apps.destinations.serializers import DestinationMiniSerializer
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
    destination = DestinationMiniSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta(ActivityCardSerializer.Meta):
        fields = ActivityCardSerializer.Meta.fields + [
            "destination", "category", "max_participants", "booking_mode", "is_featured",
        ]


class ActivityDetailSerializer(ActivityListSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)
    promo_price = serializers.SerializerMethodField()

    class Meta(ActivityListSerializer.Meta):
        fields = ActivityListSerializer.Meta.fields + ["description", "images", "promo_price"]

    def get_promo_price(self, obj):
        return money_repr(promo_price_for(obj), obj.currency, self.context.get("request"))
