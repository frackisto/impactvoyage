from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, ExchangeRate, SiteSettings
from .serializers import CategorySerializer, ExchangeRateSerializer, SiteSettingsSerializer


@extend_schema(responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}})
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({"status": "ok", "service": "voyage-api"})


class SiteSettingsView(APIView):
    """Coordonnées de l'agence, réseaux sociaux, hero, « À propos » (CdC § 5, § 19)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=SiteSettingsSerializer)
    def get(self, request):
        return Response(
            SiteSettingsSerializer(SiteSettings.load(), context={"request": request}).data
        )


class CurrencyView(APIView):
    """Devises d'affichage et taux depuis le FCFA (CdC § 36)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=ExchangeRateSerializer(many=True))
    def get(self, request):
        return Response(ExchangeRateSerializer(ExchangeRate.objects.all(), many=True).data)


@extend_schema(parameters=[OpenApiParameter("kind", enum=Category.Kind.values)])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        qs = Category.objects.all()
        kind = self.request.query_params.get("kind")
        return qs.filter(kind=kind) if kind else qs
