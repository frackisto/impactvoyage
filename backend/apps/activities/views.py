from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bookings.selectors import activity_places_left
from apps.core.api import SelectorReadOnlyViewSet

from . import selectors
from .serializers import ActivityDetailSerializer, ActivityListSerializer


class ActivityFilterParams(serializers.Serializer):
    """Moteur de recherche « Activités » (CdC § 7)."""

    destination = serializers.SlugField(required=False)
    category = serializers.SlugField(required=False)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0,
                                         required=False)
    max_hours = serializers.DecimalField(max_digits=5, decimal_places=1, min_value=0,
                                         required=False)
    date = serializers.DateField(required=False, help_text="Activités ayant encore des places ce jour-là")
    participants = serializers.IntegerField(min_value=1, max_value=50, required=False)


class ActivityAvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
    participants = serializers.IntegerField(min_value=1, max_value=50, default=1)


class ActivityAvailabilitySerializer(serializers.Serializer):
    date = serializers.DateField()
    places_left = serializers.IntegerField(allow_null=True, help_text="null : sans limite de places")
    available = serializers.BooleanField()


@extend_schema_view(list=extend_schema(parameters=[ActivityFilterParams]))
class ActivityViewSet(SelectorReadOnlyViewSet):
    """Activités et excursions : /activities, /activities/{slug}, /availability."""

    serializer_class = ActivityListSerializer
    detail_serializer_class = ActivityDetailSerializer
    filter_params_class = ActivityFilterParams
    list_selector = selectors.activity_list
    detail_selector = selectors.activity_detail
    search_fields = ["title", "short_description", "destination__name"]
    ordering_fields = ["title", "base_price", "duration_hours"]

    @extend_schema(
        parameters=[
            OpenApiParameter("date", type=str, required=True, description="AAAA-MM-JJ"),
            OpenApiParameter("participants", type=int, description="1 par défaut"),
        ],
        responses=ActivityAvailabilitySerializer,
    )
    @action(detail=True)
    def availability(self, request, slug=None):
        """Places restantes à une date."""
        activity = self.get_object()
        query = ActivityAvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        day, participants = query.validated_data["date"], query.validated_data["participants"]
        left = activity_places_left(activity, day)
        return Response(ActivityAvailabilitySerializer({
            "date": day,
            "places_left": left,
            "available": left is None or left >= participants,
        }).data)
