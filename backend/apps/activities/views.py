from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

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


@extend_schema_view(list=extend_schema(parameters=[ActivityFilterParams]))
class ActivityViewSet(SelectorReadOnlyViewSet):
    serializer_class = ActivityListSerializer
    detail_serializer_class = ActivityDetailSerializer
    filter_params_class = ActivityFilterParams
    list_selector = selectors.activity_list
    detail_selector = selectors.activity_detail
    search_fields = ["title", "short_description", "destination__name"]
    ordering_fields = ["title", "base_price", "duration_hours"]
