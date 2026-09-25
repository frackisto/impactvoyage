from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api import IsStaff

from . import selectors, services
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Notifications du tableau de bord de l'utilisateur connecté (CdC § 30)."""

    permission_classes = [IsStaff]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # génération du schéma OpenAPI
            return Notification.objects.none()
        unread = self.request.query_params.get("unread") in ("1", "true")
        return selectors.notifications_for(self.request.user, unread_only=unread)

    @extend_schema(parameters=[OpenApiParameter("unread", bool)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = services.mark_as_read(self.get_object())
        return Response(self.get_serializer(notification).data)

    @extend_schema(request=None, responses={200: {"type": "object"}})
    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        return Response({"updated": services.mark_all_as_read(request.user)})

    @extend_schema(responses={200: {"type": "object"}})
    @action(detail=False, url_path="unread-count")
    def unread_count(self, request):
        return Response({"count": selectors.unread_count(request.user)})
