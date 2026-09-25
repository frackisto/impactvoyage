from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

from apps.core.api import SelectorReadOnlyViewSet

from .models import Offer
from .selectors import offer_detail, offer_list
from .serializers import OfferDetailSerializer, OfferListSerializer


class OfferFilterParams(serializers.Serializer):
    offer_type = serializers.ChoiceField(choices=Offer.OfferType.choices, required=False)
    destination = serializers.SlugField(required=False)


@extend_schema_view(list=extend_schema(parameters=[OfferFilterParams]))
class OfferViewSet(SelectorReadOnlyViewSet):
    """Offres promotionnelles en cours (CdC § 17)."""

    serializer_class = OfferListSerializer
    detail_serializer_class = OfferDetailSerializer
    filter_params_class = OfferFilterParams
    list_selector = offer_list
    detail_selector = offer_detail
    search_fields = ["title", "short_description"]
    ordering_fields = ["end_date", "promo_price"]
