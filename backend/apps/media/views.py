from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

from apps.core.api import SelectorReadOnlyViewSet

from . import selectors
from .serializers import AlbumDetailSerializer, AlbumListSerializer


class AlbumFilterParams(serializers.Serializer):
    category = serializers.SlugField(required=False)


@extend_schema_view(list=extend_schema(parameters=[AlbumFilterParams]))
class AlbumViewSet(SelectorReadOnlyViewSet):
    """Médiathèque (CdC § 16) : /media/albums, /media/albums/{slug}."""

    serializer_class = AlbumListSerializer
    detail_serializer_class = AlbumDetailSerializer
    filter_params_class = AlbumFilterParams
    list_selector = selectors.album_list
    detail_selector = selectors.album_detail
    search_fields = ["title", "description"]
    ordering_fields = ["published_at", "title"]
