from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, serializers, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from . import selectors
from .models import VisaService
from .serializers import VisaServiceSerializer


class VisaFilterParams(serializers.Serializer):
    """Moteur de recherche « Visa » (CdC § 7)."""

    destination_country_code = serializers.RegexField(r"^[A-Za-z]{2}$", required=False)
    nationality_code = serializers.RegexField(r"^[A-Za-z]{2}$", required=False)
    purpose = serializers.ChoiceField(choices=VisaService.Purpose.choices, required=False)


@extend_schema_view(
    list=extend_schema(parameters=[VisaFilterParams]),
    retrieve=extend_schema(
        operation_id="visas_by_country", responses=VisaServiceSerializer(many=True)
    ),
)
class VisaViewSet(viewsets.ReadOnlyModelViewSet):
    """/visas (recherche) et /visas/{country_slug} : toutes les formules d'un pays."""

    permission_classes = [permissions.AllowAny]
    serializer_class = VisaServiceSerializer
    lookup_field = "country_slug"
    search_fields = ["visa_type", "description"]
    ordering_fields = ["visa_type", "fees"]

    def get_queryset(self):
        params = VisaFilterParams(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        return selectors.visa_list(**{k: v for k, v in params.validated_data.items() if v})

    def retrieve(self, request, country_slug=None):
        visas = selectors.visas_for_country(country_slug)
        if not visas.exists():
            raise NotFound()
        return Response(self.get_serializer(visas, many=True).data)
