from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.serializers import (
    GalleryImageSerializer,
    MoneyField,
    MoneySerializer,
    money_repr,
)
from apps.offers.selectors import promo_price_for

from .models import Vehicle


class VehicleListSerializer(serializers.ModelSerializer):
    """L'immatriculation n'est jamais exposée publiquement."""

    price_per_day = MoneyField(amount="base_price")

    class Meta:
        model = Vehicle
        fields = [
            "id", "slug", "brand", "model", "category", "year", "seats", "transmission",
            "fuel", "air_conditioning", "cover_image", "cover_alt", "price_per_day",
            "is_featured",
        ]


class VehicleDetailSerializer(VehicleListSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)
    promo_price = serializers.SerializerMethodField()

    class Meta(VehicleListSerializer.Meta):
        fields = VehicleListSerializer.Meta.fields + [
            "description", "features", "images", "booking_mode", "promo_price",
        ]

    @extend_schema_field(MoneySerializer(allow_null=True))
    def get_promo_price(self, obj):
        return money_repr(promo_price_for(obj), obj.currency, self.context.get("request"))
