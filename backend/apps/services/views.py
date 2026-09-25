from apps.core.api import SelectorReadOnlyViewSet

from . import selectors
from .models import Service
from .serializers import ServiceSerializer


class ServiceViewSet(SelectorReadOnlyViewSet):
    """Prestations de l'agence (CdC § 11), dans l'ordre défini dans l'admin."""

    serializer_class = ServiceSerializer
    list_selector = selectors.service_list
    detail_selector = staticmethod(lambda slug: Service.objects.published().get(slug=slug))
    pagination_class = None
