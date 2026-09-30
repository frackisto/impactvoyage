from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.response import Response

from apps.core.api import WriteThrottleMixin

from . import selectors, services
from .models import REVIEW_TARGETS
from .serializers import ReviewCreateSerializer, ReviewSerializer


class ReviewFilterParams(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=REVIEW_TARGETS, required=False)
    target_slug = serializers.SlugField(required=False)
    featured = serializers.BooleanField(required=False, allow_null=True, default=None)


@extend_schema_view(list=extend_schema(parameters=[ReviewFilterParams]))
class ReviewViewSet(WriteThrottleMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Avis clients (CdC § 20). GET : avis validés, filtrables par page
    (?target_type=tour&target_slug=…) ou mis en avant (?featured=true, accueil).
    POST : dépôt d'un avis, publié après modération.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = ReviewSerializer
    write_throttle_scope = "reviews"
    ordering_fields = ["created_at", "rating"]

    def get_queryset(self):
        params = ReviewFilterParams(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data
        target = {}
        if data.get("target_type") and data.get("target_slug"):
            target = {f"{data['target_type']}__slug": data["target_slug"]}
        qs = selectors.approved_reviews(**target)
        if data.get("featured"):
            qs = qs.filter(is_featured=True)
        return qs

    @extend_schema(
        request={"multipart/form-data": ReviewCreateSerializer,
                 "application/json": ReviewCreateSerializer},
        responses={201: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    def create(self, request):
        payload = ReviewCreateSerializer(data=request.data, context={"request": request})
        payload.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        services.submit_review(**payload.validated_data, user=user)
        return Response(
            {"message": "Merci ! Votre avis sera publié après validation."},
            status=status.HTTP_201_CREATED,
        )
