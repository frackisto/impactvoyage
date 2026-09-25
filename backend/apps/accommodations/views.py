from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

from apps.core.api import SelectorReadOnlyViewSet
from apps.core.filters import CommaSeparatedIntegerField, PeriodParams, PriceRangeParams

from . import selectors
from .models import Hotel
from .serializers import (
    HotelDetailSerializer,
    HotelListSerializer,
    ResidenceDetailSerializer,
    ResidenceListSerializer,
)


class HotelFilterParams(PriceRangeParams):
    """Moteur de recherche « Hôtels » (CdC § 7, § 14)."""

    destination = serializers.SlugField(required=False)
    accommodation_type = serializers.ChoiceField(
        choices=Hotel.AccommodationType.choices, required=False
    )
    stars = serializers.IntegerField(min_value=1, max_value=5, required=False)
    amenities = CommaSeparatedIntegerField(required=False)
    travelers = serializers.IntegerField(min_value=1, max_value=20, required=False)


class ResidenceFilterParams(PeriodParams, PriceRangeParams):
    destination = serializers.SlugField(required=False)
    min_capacity = serializers.IntegerField(min_value=1, required=False)
    min_rooms = serializers.IntegerField(min_value=1, required=False)
    amenities = CommaSeparatedIntegerField(required=False)
    available_from = serializers.DateField(required=False)
    available_to = serializers.DateField(required=False)


@extend_schema_view(list=extend_schema(parameters=[HotelFilterParams]))
class HotelViewSet(SelectorReadOnlyViewSet):
    """Hôtels, appartements, partenaires : /hotels, /hotels/{slug}."""

    serializer_class = HotelListSerializer
    detail_serializer_class = HotelDetailSerializer
    filter_params_class = HotelFilterParams
    list_selector = selectors.hotel_list
    detail_selector = selectors.hotel_detail
    search_fields = ["name", "short_description", "destination__name", "address"]
    ordering_fields = ["name", "price_from", "stars", "rating_avg"]


@extend_schema_view(list=extend_schema(parameters=[ResidenceFilterParams]))
class ResidenceViewSet(SelectorReadOnlyViewSet):
    """Résidences meublées (CdC § 13) : /residences, /residences/{slug}."""

    serializer_class = ResidenceListSerializer
    detail_serializer_class = ResidenceDetailSerializer
    filter_params_class = ResidenceFilterParams
    list_selector = selectors.residence_list
    detail_selector = selectors.residence_detail
    search_fields = ["name", "short_description", "destination__name", "address"]
    ordering_fields = ["name", "base_price", "capacity"]
