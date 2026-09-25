from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

from apps.core.api import SelectorReadOnlyViewSet

from . import selectors
from .models import TransportService
from .serializers import TransportServiceSerializer


class TransportFilterParams(serializers.Serializer):
    """Moteur de recherche « Transport » (CdC § 7)."""

    transport_type = serializers.ChoiceField(
        choices=TransportService.TransportType.choices, required=False
    )
    origin = serializers.CharField(required=False, max_length=150)
    destination = serializers.CharField(required=False, max_length=150)
    passengers = serializers.IntegerField(min_value=1, max_value=99, required=False)


@extend_schema_view(list=extend_schema(parameters=[TransportFilterParams]))
class TransportViewSet(SelectorReadOnlyViewSet):
    serializer_class = TransportServiceSerializer
    filter_params_class = TransportFilterParams
    list_selector = selectors.transport_list
    detail_selector = staticmethod(
        lambda slug: TransportService.objects.published().get(slug=slug)
    )
    search_fields = ["title", "origin", "destination"]
    ordering_fields = ["price_from", "title"]
