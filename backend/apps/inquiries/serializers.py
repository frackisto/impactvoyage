"""
Devis et contact. Les serializers d'entrée valident les données ; la vue appelle
ensuite le service (inquiries.services) avec serializer.validated_data.
"""
import re

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.activities.models import Activity
from apps.core.serializers import HoneypotSerializerMixin, MoneyField
from apps.destinations.models import Destination
from apps.offers.models import Offer
from apps.tours.models import Tour

from .models import ContactMessage, QuoteRequest

PHONE_RE = re.compile(r"^\+?[0-9 ().-]{6,20}$")


def validate_phone(value):
    if value and not PHONE_RE.match(value):
        raise serializers.ValidationError("Numéro de téléphone invalide.")
    return value


def validate_country_code(value):
    if value and not re.fullmatch(r"[A-Za-z]{2}", value):
        raise serializers.ValidationError("Code pays ISO à 2 lettres attendu (ex. CI).")
    return value.upper()


class QuoteRequestCreateSerializer(HoneypotSerializerMixin, serializers.ModelSerializer):
    """Formulaire /devis (CdC § 18)."""

    destination = serializers.SlugRelatedField(
        slug_field="slug", queryset=Destination.objects.published(), required=False,
        allow_null=True,
    )
    activities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Activity.objects.published(), required=False
    )
    source_tour = serializers.SlugRelatedField(
        slug_field="slug", queryset=Tour.objects.published(), required=False, allow_null=True
    )
    source_offer = serializers.SlugRelatedField(
        slug_field="slug", queryset=Offer.objects.all(), required=False, allow_null=True
    )
    consent = serializers.BooleanField(write_only=True)

    class Meta:
        model = QuoteRequest
        fields = [
            "first_name", "last_name", "email", "phone", "whatsapp", "country_code",
            "destination_text", "destination", "date_departure", "date_return", "adults",
            "children", "travel_type", "budget", "currency", "accommodation_pref",
            "transport_pref", "activities", "services_requested", "comments", "source_tour",
            "source_offer", "consent", "website",
        ]
        extra_kwargs = {"adults": {"min_value": 1, "max_value": 99},
                        "children": {"max_value": 99}}

    validate_phone = staticmethod(validate_phone)
    validate_whatsapp = staticmethod(validate_phone)
    validate_country_code = staticmethod(validate_country_code)

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError(
                "Vous devez accepter le traitement de vos données pour envoyer la demande."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        departure, back = attrs.get("date_departure"), attrs.get("date_return")
        if departure and departure < timezone.localdate():
            raise serializers.ValidationError({"date_departure": "Cette date est déjà passée."})
        if departure and back and back < departure:
            raise serializers.ValidationError(
                {"date_return": "Le retour doit suivre le départ."}
            )
        if not attrs.get("destination") and not attrs.get("destination_text"):
            raise serializers.ValidationError(
                {"destination_text": "Indiquez la destination souhaitée."}
            )
        return attrs


class QuoteClientSerializer(serializers.ModelSerializer):
    """Vue client via le lien secret : sa demande et la proposition de l'agence."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    proposal_amount = MoneyField(amount="proposal_amount")
    can_answer = serializers.SerializerMethodField()
    booking_reference = serializers.CharField(
        source="booking.reference", read_only=True, default=None
    )

    class Meta:
        model = QuoteRequest
        fields = [
            "reference", "status", "status_label", "first_name", "last_name",
            "destination_text", "date_departure", "date_return", "adults", "children",
            "services_requested", "proposal_amount", "proposal_message",
            "proposal_valid_until", "can_answer", "booking_reference", "created_at",
        ]

    def get_can_answer(self, obj) -> bool:
        return obj.status == QuoteRequest.Status.DEVIS_ENVOYE and (
            obj.proposal_valid_until is None
            or obj.proposal_valid_until >= timezone.localdate()
        )


class QuoteDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class StaffMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class QuoteStaffSerializer(serializers.ModelSerializer):
    """Fiche complète pour l'équipe (jamais le jeton d'accès client)."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    destination = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    assigned_to = serializers.SerializerMethodField()
    budget = MoneyField(amount="budget")
    proposal_amount = MoneyField(amount="proposal_amount")

    class Meta:
        model = QuoteRequest
        exclude = ["access_token", "deleted_at", "activities"]

    @extend_schema_field(StaffMemberSerializer(allow_null=True))
    def get_assigned_to(self, obj):
        user = obj.assigned_to
        return {"id": user.pk, "name": str(user)} if user else None


class QuoteProposalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    message = serializers.CharField(max_length=5000)
    valid_until = serializers.DateField()

    def validate_valid_until(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("La date de validité est déjà passée.")
        return value


class QuoteAssignSerializer(serializers.Serializer):
    commercial = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_staff=True, is_active=True)
    )


class QuoteStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=QuoteRequest.Status.choices)


class ContactMessageCreateSerializer(HoneypotSerializerMixin, serializers.ModelSerializer):
    """Formulaire /contact (CdC § 19)."""

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message", "website"]
        extra_kwargs = {"message": {"min_length": 10, "max_length": 5000}}

    validate_phone = staticmethod(validate_phone)


class ContactMessageStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "phone", "subject", "message", "status", "created_at"]
