from django.utils.translation import get_language
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.core.api import IsStaff, WriteThrottleMixin

from . import selectors, services
from .models import Booking
from .serializers import (
    BookingDecisionSerializer,
    BookingRequestSerializer,
    BookingSerializer,
    BookingStaffSerializer,
)

# Le client peut annuler lui-même tant que la réservation n'est pas confirmée ;
# ensuite, l'annulation passe par l'agence (CdC § 11 « changements et annulations »).
CUSTOMER_CANCELLABLE = {Booking.Status.REQUESTED, Booking.Status.PENDING}


class BookingViewSet(WriteThrottleMixin, viewsets.GenericViewSet):
    """
    Réservations (architecture § 3.8).
    Public : POST /bookings/ (demande). Client connecté : ses réservations,
    annulation avant confirmation. Équipe : toutes, confirmation, refus, annulation.
    """

    lookup_field = "reference"
    write_throttle_scope = "bookings"
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        if self.action in ("confirm", "reject"):
            return [IsStaff()]
        return [permissions.IsAuthenticated()]

    def _is_staff(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # génération du schéma OpenAPI
            return Booking.objects.none()
        if self._is_staff():
            return selectors.booking_detail_queryset()
        return selectors.bookings_for_user(self.request.user)

    def get_serializer_class(self):
        return BookingStaffSerializer if self._is_staff() else BookingSerializer

    @extend_schema(request=BookingRequestSerializer, responses={201: BookingSerializer})
    def create(self, request):
        payload = BookingRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        booking = services.request_booking(
            **payload.validated_data,
            user=request.user if request.user.is_authenticated else None,
            language=get_language(),
        )
        return Response(
            BookingSerializer(booking, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(parameters=[OpenApiParameter("status", enum=Booking.Status.values)])
    def list(self, request):
        bookings = self.get_queryset()
        if status_filter := request.query_params.get("status"):
            bookings = bookings.filter(status=status_filter)
        page = self.paginate_queryset(bookings)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def retrieve(self, request, reference=None):
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(request=BookingDecisionSerializer)
    @action(detail=True, methods=["post"])
    def confirm(self, request, reference=None):
        payload = BookingDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        notes = payload.validated_data.get("reason")
        booking = services.confirm_booking(self.get_object(), internal_notes=notes)
        return Response(self.get_serializer(booking).data)

    @extend_schema(request=BookingDecisionSerializer)
    @action(detail=True, methods=["post"])
    def reject(self, request, reference=None):
        payload = BookingDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        booking = services.reject_booking(
            self.get_object(), reason=payload.validated_data.get("reason", "")
        )
        return Response(self.get_serializer(booking).data)

    @extend_schema(request=BookingDecisionSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, reference=None):
        payload = BookingDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        booking = self.get_object()
        by_customer = not self._is_staff()
        if by_customer and booking.status not in CUSTOMER_CANCELLABLE:
            raise PermissionDenied(
                "Cette réservation est confirmée : contactez l'agence pour l'annuler."
            )
        booking = services.cancel_booking(
            booking, reason=payload.validated_data.get("reason", ""), by_customer=by_customer
        )
        return Response(self.get_serializer(booking).data)
