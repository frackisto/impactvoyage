from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bookings.selectors import vehicle_booked_periods, vehicle_is_available
from apps.core.api import SelectorReadOnlyViewSet
from apps.core.filters import PeriodParams

from . import selectors
from .models import Vehicle
from .serializers import AvailabilityQuerySerializer, VehicleDetailSerializer, VehicleListSerializer


class VehicleFilterParams(PeriodParams):
    category = serializers.ChoiceField(choices=Vehicle.Category.choices, required=False)
    transmission = serializers.ChoiceField(choices=Vehicle.Transmission.choices, required=False)
    min_seats = serializers.IntegerField(min_value=1, required=False)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0,
                                         required=False)
    available_from = serializers.DateField(required=False)
    available_to = serializers.DateField(required=False)


class AvailabilitySerializer(serializers.Serializer):
    available = serializers.BooleanField()
    booked_periods = serializers.ListField(child=serializers.ListField(child=serializers.DateField()))


@extend_schema_view(list=extend_schema(parameters=[VehicleFilterParams]))
class VehicleViewSet(SelectorReadOnlyViewSet):
    """Location de véhicules (CdC § 12) : /vehicles, /vehicles/{slug}, /availability."""

    serializer_class = VehicleListSerializer
    detail_serializer_class = VehicleDetailSerializer
    filter_params_class = VehicleFilterParams
    list_selector = selectors.vehicle_list
    detail_selector = selectors.vehicle_detail
    search_fields = ["brand", "model"]
    ordering_fields = ["base_price", "seats", "year"]

    @extend_schema(
        parameters=[OpenApiParameter("start", type=str, required=True),
                    OpenApiParameter("end", type=str, required=True)],
        responses=AvailabilitySerializer,
    )
    @action(detail=True)
    def availability(self, request, slug=None):
        """Disponibilité sur une période [start, end) et périodes déjà réservées."""
        vehicle = self.get_object()
        query = AvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        start, end = query.validated_data["start"], query.validated_data["end"]
        return Response({
            "available": vehicle_is_available(vehicle, start, end),
            "booked_periods": vehicle_booked_periods(vehicle, start),
        })
