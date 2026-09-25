from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.serializers import MoneyField
from apps.destinations.references import DestinationMiniSerializer

from .models import Offer


class OfferTargetSerializer(serializers.Serializer):
    type = serializers.CharField(help_text="tour, hotel, residence, vehicle ou activity")
    slug = serializers.CharField()
    title = serializers.CharField()


class OfferListSerializer(serializers.ModelSerializer):
    initial_price = MoneyField(amount="initial_price")
    promo_price = MoneyField(amount="promo_price")
    discount_percent = serializers.IntegerField(read_only=True)
    badge = serializers.CharField(source="display_badge", read_only=True)
    target = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            "id", "slug", "title", "short_description", "offer_type", "initial_price",
            "promo_price", "discount_percent", "start_date", "end_date", "seats_available",
            "badge", "cover_image", "cover_alt", "target",
        ]

    @extend_schema_field(OfferTargetSerializer(allow_null=True))
    def get_target(self, obj):
        """Lien vers la fiche concernée : {"type": "tour", "slug": "…", "title": "…"}."""
        target = obj.target
        if target is None:
            return None
        title = getattr(target, "title", None) or getattr(target, "name", None)
        if title is None:  # véhicule
            title = f"{target.brand} {target.model}"
        return {"type": target._meta.model_name, "slug": target.slug, "title": title}


class OfferDetailSerializer(OfferListSerializer):
    destination = DestinationMiniSerializer(read_only=True)

    class Meta(OfferListSerializer.Meta):
        fields = OfferListSerializer.Meta.fields + ["description", "conditions", "destination"]
