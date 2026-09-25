from django.utils.translation import get_language
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bookings.serializers import BookingSerializer
from apps.core.api import WriteThrottleMixin, has_perm

from . import selectors, services
from .models import QuoteRequest
from .serializers import (
    ContactMessageCreateSerializer,
    QuoteAssignSerializer,
    QuoteClientSerializer,
    QuoteDeclineSerializer,
    QuoteProposalSerializer,
    QuoteRequestCreateSerializer,
    QuoteStaffSerializer,
    QuoteStatusSerializer,
)

CLIENT_ACTIONS = ("create", "retrieve", "accept", "decline")
CanViewQuotes = has_perm("inquiries.view_quoterequest")
CanChangeQuotes = has_perm("inquiries.change_quoterequest")


class QuoteTokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class QuoteDeclineRequestSerializer(QuoteTokenSerializer, QuoteDeclineSerializer):
    pass


class QuoteViewSet(WriteThrottleMixin, viewsets.GenericViewSet):
    """
    Devis (CdC § 18, § 38).
    Public : POST /quotes/ ; le client consulte (?token=) puis accepte ou décline
    avec le jeton reçu par email. Équipe : liste, fiche, assignation, proposition, statut.
    """

    lookup_field = "reference"
    write_throttle_scope = "quotes"
    throttled_actions = ("create", "accept", "decline")
    serializer_class = QuoteStaffSerializer

    def get_permissions(self):
        if self.action in CLIENT_ACTIONS:
            return [permissions.AllowAny()]
        if self.action == "list":
            return [CanViewQuotes()]
        return [CanChangeQuotes()]

    def get_queryset(self):
        return selectors.quote_queryset()

    @extend_schema(request=QuoteRequestCreateSerializer, responses={201: QuoteClientSerializer})
    def create(self, request):
        serializer = QuoteRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        quote = services.create_quote_request(
            activities=data.pop("activities", []), language=get_language(), **data
        )
        return Response(QuoteClientSerializer(quote).data, status=status.HTTP_201_CREATED)

    @extend_schema(parameters=[OpenApiParameter("status", enum=QuoteRequest.Status.values)])
    def list(self, request):
        quotes = selectors.quotes_for_staff(status=request.query_params.get("status"))
        page = self.paginate_queryset(quotes)
        return self.get_paginated_response(QuoteStaffSerializer(page, many=True).data)

    @extend_schema(
        parameters=[OpenApiParameter("token", description="Jeton du lien client")],
        responses=QuoteClientSerializer,
    )
    def retrieve(self, request, reference=None):
        """Équipe : fiche complète. Client : sa demande, avec le jeton reçu par email."""
        if CanViewQuotes().has_permission(request, self):
            return Response(QuoteStaffSerializer(self.get_object()).data)
        quote = services.get_quote_for_client(reference, request.query_params.get("token", ""))
        return Response(QuoteClientSerializer(quote).data)

    @extend_schema(request=QuoteTokenSerializer, responses=BookingSerializer)
    @action(detail=True, methods=["post"])
    def accept(self, request, reference=None):
        payload = QuoteTokenSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        booking = services.accept_quote(reference, payload.validated_data["token"])
        return Response(BookingSerializer(booking, context={"request": request}).data)

    @extend_schema(request=QuoteDeclineRequestSerializer, responses=QuoteClientSerializer)
    @action(detail=True, methods=["post"])
    def decline(self, request, reference=None):
        payload = QuoteDeclineRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        quote = services.decline_quote(
            reference, payload.validated_data["token"], payload.validated_data.get("reason", "")
        )
        return Response(QuoteClientSerializer(quote).data)

    @extend_schema(request=QuoteProposalSerializer, responses=QuoteStaffSerializer)
    @action(detail=True, methods=["post"], url_path="send-proposal")
    def send_proposal(self, request, reference=None):
        payload = QuoteProposalSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        quote = services.send_proposal(self.get_object(), by=request.user, **payload.validated_data)
        return Response(QuoteStaffSerializer(quote).data)

    @extend_schema(request=QuoteAssignSerializer, responses=QuoteStaffSerializer)
    @action(detail=True, methods=["post"])
    def assign(self, request, reference=None):
        payload = QuoteAssignSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        quote = services.assign_quote(self.get_object(), payload.validated_data["commercial"])
        return Response(QuoteStaffSerializer(quote).data)

    @extend_schema(request=QuoteStatusSerializer, responses=QuoteStaffSerializer)
    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, reference=None):
        payload = QuoteStatusSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        quote = services.change_quote_status(self.get_object(), payload.validated_data["status"])
        return Response(QuoteStaffSerializer(quote).data)


class ContactMessageViewSet(WriteThrottleMixin, viewsets.GenericViewSet):
    """Formulaire de contact (CdC § 19) : POST /contact/."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ContactMessageCreateSerializer
    write_throttle_scope = "contact"

    @extend_schema(responses={201: {"type": "object", "properties": {"message": {"type": "string"}}}})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.create_contact_message(**serializer.validated_data)
        return Response(
            {"message": "Votre message a bien été envoyé. Nous vous répondons rapidement."},
            status=status.HTTP_201_CREATED,
        )
