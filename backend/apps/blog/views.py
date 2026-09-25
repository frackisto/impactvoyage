from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers

from apps.core.api import SelectorReadOnlyViewSet

from . import selectors
from .serializers import BlogPostDetailSerializer, BlogPostListSerializer


class BlogFilterParams(serializers.Serializer):
    category = serializers.SlugField(required=False)
    tag = serializers.SlugField(required=False)


@extend_schema_view(list=extend_schema(parameters=[BlogFilterParams]))
class BlogPostViewSet(SelectorReadOnlyViewSet):
    """Blog / conseils voyage (CdC § 21)."""

    serializer_class = BlogPostListSerializer
    detail_serializer_class = BlogPostDetailSerializer
    filter_params_class = BlogFilterParams
    list_selector = selectors.post_list
    detail_selector = selectors.post_detail
    search_fields = ["title", "excerpt"]
    ordering_fields = ["published_at", "title"]
