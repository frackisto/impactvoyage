from rest_framework import serializers

from apps.core.serializers import GalleryImageSerializer, MoneyField, money_repr
from apps.destinations.serializers import DestinationMiniSerializer
from apps.offers.selectors import promo_price_for
from apps.reviews.selectors import rating_summary

from .models import Amenity, Hotel, Residence, Room


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["id", "name", "icon"]


class HotelCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = [
            "id", "slug", "name", "short_description", "accommodation_type", "stars",
            "cover_image", "cover_alt",
        ]


class HotelListSerializer(HotelCardSerializer):
    """Carte de résultat : price_from et rating_* viennent de accommodations.selectors.hotel_list."""

    destination = DestinationMiniSerializer(read_only=True)
    # Les chambres sont tarifées en FCFA : pas d'attribut devise sur l'hôtel.
    price_from = MoneyField(amount="price_from", currency="price_from_currency")
    rating_avg = serializers.FloatField(read_only=True, default=None)
    rating_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(HotelCardSerializer.Meta):
        fields = HotelCardSerializer.Meta.fields + [
            "destination", "address", "is_featured", "price_from", "rating_avg", "rating_count",
        ]


class RoomSerializer(serializers.ModelSerializer):
    price_per_night = MoneyField(amount="base_price")

    class Meta:
        model = Room
        fields = ["id", "name", "description", "capacity", "price_per_night", "booking_mode"]


class HotelDetailSerializer(HotelCardSerializer):
    destination = DestinationMiniSerializer(read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    images = GalleryImageSerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta(HotelCardSerializer.Meta):
        fields = HotelCardSerializer.Meta.fields + [
            "description", "destination", "address", "amenities", "images", "rooms", "rating",
        ]

    def get_rating(self, obj):
        return rating_summary(hotel=obj)


class ResidenceListSerializer(serializers.ModelSerializer):
    destination = DestinationMiniSerializer(read_only=True)
    price_per_night = MoneyField(amount="base_price")

    class Meta:
        model = Residence
        fields = [
            "id", "slug", "name", "short_description", "destination", "address",
            "rooms_count", "capacity", "cover_image", "cover_alt", "price_per_night",
            "is_featured",
        ]


class ResidenceDetailSerializer(ResidenceListSerializer):
    amenities = AmenitySerializer(many=True, read_only=True)
    images = GalleryImageSerializer(many=True, read_only=True)
    promo_price = serializers.SerializerMethodField()

    class Meta(ResidenceListSerializer.Meta):
        fields = ResidenceListSerializer.Meta.fields + [
            "description", "amenities", "services", "conditions", "images", "booking_mode",
            "promo_price",
        ]

    def get_promo_price(self, obj):
        return money_repr(promo_price_for(obj), obj.currency, self.context.get("request"))
