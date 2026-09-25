from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api import SelectorReadOnlyViewSet
from apps.core.filters import PriceRangeParams
from apps.destinations.models import Destination

from . import selectors
from .models import Tour
from .serializers import TourDepartureSerializer, TourDetailSerializer, TourListSerializer


class TourFilterParams(PriceRangeParams):
    """Moteur de recherche « Tours » (CdC § 7, § 10)."""

    scope = serializers.ChoiceField(choices=Tour.Scope.choices, required=False)
    theme = serializers.SlugField(required=False)
    destination = serializers.SlugField(required=False)
    continent = serializers.ChoiceField(choices=Destination.Continent.choices, required=False)
    country_code = serializers.RegexField(r"^[A-Za-z]{2}$", required=False)
    max_days = serializers.IntegerField(min_value=1, required=False)
    departure_from = serializers.DateField(required=False)
    departure_to = serializers.DateField(required=False)
    travelers = serializers.IntegerField(min_value=1, max_value=99, required=False)

    def validate_country_code(self, value):
        return value.upper()


@extend_schema_view(list=extend_schema(parameters=[TourFilterParams]))
class TourViewSet(SelectorReadOnlyViewSet):
    """Circuits nationaux et internationaux : /tours, /tours/{slug}, /tours/{slug}/departures."""

    serializer_class = TourListSerializer
    detail_serializer_class = TourDetailSerializer
    filter_params_class = TourFilterParams
    list_selector = selectors.tour_list
    detail_selector = selectors.tour_detail
    search_fields = ["title", "short_description", "destination__name"]
    ordering_fields = ["base_price", "duration_days", "next_departure", "title", "rating_avg"]

    @extend_schema(responses=TourDepartureSerializer(many=True))
    @action(detail=True, pagination_class=None)
    def departures(self, request, slug=None):
        """Départs réservables (ouverts, à venir, avec des places)."""
        tour = self.get_object()
        return Response(
            TourDepartureSerializer(
                tour.open_departures, many=True, context=self.get_serializer_context()
            ).data
        )
