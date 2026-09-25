from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

from apps.core.api import SelectorReadOnlyViewSet

from . import selectors
from .models import Event
from .serializers import EventDetailSerializer, EventListSerializer


class EventFilterParams(serializers.Serializer):
    category = serializers.ChoiceField(choices=Event.Category.choices, required=False)
    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)


@extend_schema_view(list=extend_schema(parameters=[EventFilterParams]))
class EventViewSet(SelectorReadOnlyViewSet):
    """Événementiel (CdC § 15)."""

    serializer_class = EventListSerializer
    detail_serializer_class = EventDetailSerializer
    filter_params_class = EventFilterParams
    list_selector = selectors.event_list
    detail_selector = selectors.event_detail
    search_fields = ["title", "short_description", "location"]
    ordering_fields = ["date", "title"]
