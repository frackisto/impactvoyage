from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

from apps.core.api import SelectorReadOnlyViewSet

from . import selectors
from .models import Destination
from .serializers import DestinationDetailSerializer, DestinationListSerializer


class DestinationFilterParams(serializers.Serializer):
    continent = serializers.ChoiceField(choices=Destination.Continent.choices, required=False)
    country = serializers.RegexField(
        r"^[A-Za-z]{2}$", required=False, help_text="Code pays ISO 3166-1, ex. CI"
    )
    featured = serializers.BooleanField(required=False, allow_null=True, default=None)


@extend_schema_view(list=extend_schema(parameters=[DestinationFilterParams]))
class DestinationViewSet(SelectorReadOnlyViewSet):
    """Destinations (CdC § 8) : /destinations, /destinations/{slug}."""

    serializer_class = DestinationListSerializer
    detail_serializer_class = DestinationDetailSerializer
    filter_params_class = DestinationFilterParams
    list_selector = selectors.destination_list
    detail_selector = selectors.destination_detail
    search_fields = ["name", "city", "short_description"]
    ordering_fields = ["name", "tours_count"]
