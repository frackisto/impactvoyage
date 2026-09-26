from math import ceil

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bookings.selectors import booked_periods, residence_is_available
from apps.core.api import SelectorReadOnlyViewSet
from apps.core.filters import (
    AvailabilityQuerySerializer,
    CommaSeparatedIntegerField,
    PeriodParams,
    PriceRangeParams,
)
from apps.core.serializers import AvailabilitySerializer

from . import selectors
from .models import Hotel
from .serializers import (
    AmenitySerializer,
    HotelDetailSerializer,
    HotelListSerializer,
    ResidenceDetailSerializer,
    ResidenceListSerializer,
)


class HotelFilterParams(PeriodParams, PriceRangeParams):
    """Moteur de recherche « Hôtels » (CdC § 7, § 14)."""

    destination = serializers.SlugField(required=False)
    accommodation_type = serializers.ChoiceField(
        choices=Hotel.AccommodationType.choices, required=False
    )
    stars = serializers.IntegerField(min_value=1, max_value=5, required=False)
    amenities = CommaSeparatedIntegerField(required=False)
    travelers = serializers.IntegerField(min_value=1, max_value=20, required=False)
    rooms = serializers.IntegerField(min_value=1, max_value=10, required=False)
    available_from = serializers.DateField(required=False)
    available_to = serializers.DateField(required=False)


class ResidenceFilterParams(PeriodParams, PriceRangeParams):
    destination = serializers.SlugField(required=False)
    min_capacity = serializers.IntegerField(min_value=1, required=False)
    min_rooms = serializers.IntegerField(min_value=1, required=False)
    amenities = CommaSeparatedIntegerField(required=False)
    available_from = serializers.DateField(required=False)
    available_to = serializers.DateField(required=False)


class RoomAvailabilityQuerySerializer(AvailabilityQuerySerializer):
    rooms = serializers.IntegerField(min_value=1, max_value=10, default=1)
    travelers = serializers.IntegerField(min_value=1, max_value=20, required=False)


class RoomAvailabilitySerializer(serializers.Serializer):
    room = serializers.IntegerField(help_text="Identifiant du type de chambre")
    units_left = serializers.IntegerField(help_text="Chambres encore libres sur la période")
    fits = serializers.BooleanField(help_text="Capacité suffisante pour les voyageurs")
    available = serializers.BooleanField(help_text="Assez de chambres libres et capacité suffisante")


PERIOD_PARAMETERS = [
    OpenApiParameter("start", type=str, required=True, description="Arrivée (AAAA-MM-JJ)"),
    OpenApiParameter("end", type=str, required=True, description="Départ (AAAA-MM-JJ, exclu)"),
]


@extend_schema_view(list=extend_schema(parameters=[HotelFilterParams]))
class HotelViewSet(SelectorReadOnlyViewSet):
    """Hôtels, appartements, partenaires : /hotels, /hotels/{slug}, /availability."""

    serializer_class = HotelListSerializer
    detail_serializer_class = HotelDetailSerializer
    filter_params_class = HotelFilterParams
    list_selector = selectors.hotel_list
    detail_selector = selectors.hotel_detail
    search_fields = ["name", "short_description", "destination__name", "address"]
    ordering_fields = ["name", "price_from", "stars", "rating_avg"]

    @extend_schema(
        parameters=PERIOD_PARAMETERS + [
            OpenApiParameter("rooms", type=int, description="Chambres souhaitées (1 par défaut)"),
            OpenApiParameter("travelers", type=int, description="Voyageurs au total"),
        ],
        responses=RoomAvailabilitySerializer(many=True),
    )
    @action(detail=True, pagination_class=None)
    def availability(self, request, slug=None):
        """Chambres libres par type de chambre sur la période [start, end)."""
        hotel = self.get_object()
        query = RoomAvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        rooms, travelers = data["rooms"], data.get("travelers")
        result = []
        for room in selectors.room_availability(hotel, data["start"], data["end"]):
            fits = not travelers or room.capacity >= ceil(travelers / rooms)
            result.append({
                "room": room.pk,
                "units_left": max(room.units_left, 0),
                "fits": fits,
                "available": fits and room.units_left >= rooms,
            })
        return Response(RoomAvailabilitySerializer(result, many=True).data)


@extend_schema_view(list=extend_schema(parameters=[ResidenceFilterParams]))
class ResidenceViewSet(SelectorReadOnlyViewSet):
    """Résidences meublées (CdC § 13) : /residences, /residences/{slug}, /availability."""

    serializer_class = ResidenceListSerializer
    detail_serializer_class = ResidenceDetailSerializer
    filter_params_class = ResidenceFilterParams
    list_selector = selectors.residence_list
    detail_selector = selectors.residence_detail
    search_fields = ["name", "short_description", "destination__name", "address"]
    ordering_fields = ["name", "base_price", "capacity"]

    @extend_schema(parameters=PERIOD_PARAMETERS, responses=AvailabilitySerializer)
    @action(detail=True)
    def availability(self, request, slug=None):
        """Disponibilité sur une période [start, end) et périodes déjà réservées."""
        residence = self.get_object()
        query = AvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        start, end = query.validated_data["start"], query.validated_data["end"]
        return Response({
            "available": residence_is_available(residence, start, end),
            "booked_periods": booked_periods(start, residence=residence),
        })


class AmenityFilterParams(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["hotel", "residence"], default="hotel")


@extend_schema(parameters=[AmenityFilterParams])
class AmenityListView(generics.ListAPIView):
    """Équipements proposés par au moins un hébergement publié (filtres des listes)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = AmenitySerializer
    pagination_class = None

    def get_queryset(self):
        params = AmenityFilterParams(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        return selectors.amenities_in_use(params.validated_data["kind"])
