from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.serializers import HoneypotSerializerMixin, MoneyField
from apps.inquiries.serializers import validate_phone

from .models import BOOKING_TARGETS, Booking, BookingItem
from .services import CUSTOMER_CANCELLABLE, ItemRequest

# Champs de dates attendus selon le type d'offre (voir services.ItemRequest).
PERIOD_KINDS = {"room", "residence", "vehicle"}


class BookingItemRequestSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=BOOKING_TARGETS)
    object_id = serializers.IntegerField(min_value=1)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, max_value=50, default=1)
    pickup_location = serializers.CharField(required=False, allow_blank=True, max_length=200)
    dropoff_location = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate(self, attrs):
        kind = attrs["kind"]
        start, end = attrs.get("start_date"), attrs.get("end_date")
        if kind in PERIOD_KINDS:
            if not start or not end:
                raise serializers.ValidationError("Dates de début et de fin obligatoires.")
            if end <= start:
                raise serializers.ValidationError({"end_date": "La fin doit suivre le début."})
        elif kind == "activity" and not start:
            raise serializers.ValidationError({"start_date": "Choisissez une date."})
        return attrs


class BookingRequestSerializer(HoneypotSerializerMixin, serializers.Serializer):
    """
    Demande de réservation publique (CdC § 12, § 13). validated_data est prêt
    pour bookings.services.request_booking : items est une liste d'ItemRequest.
    Aucun prix n'est accepté en entrée.
    """

    contact_name = serializers.CharField(max_length=200)
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=30, validators=[validate_phone])
    customer_comments = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    items = BookingItemRequestSerializer(many=True, allow_empty=False, max_length=10)
    consent = serializers.BooleanField()

    def validate_items(self, items):
        return [ItemRequest(**item) for item in items]

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError(
                "Vous devez accepter le traitement de vos données pour envoyer la demande."
            )
        return value


class BookingItemSerializer(serializers.ModelSerializer):
    kind = serializers.SerializerMethodField()
    target_slug = serializers.SerializerMethodField()
    unit_price = MoneyField(amount="unit_price", currency="booking.currency")
    line_total = MoneyField(amount="line_total", currency="booking.currency")

    class Meta:
        model = BookingItem
        fields = [
            "kind", "target_slug", "label", "start_date", "end_date", "quantity", "unit_price",
            "line_total", "pickup_location", "dropoff_location",
        ]

    @extend_schema_field(serializers.ChoiceField(choices=BOOKING_TARGETS))
    def get_kind(self, obj):
        return next(k for k in BOOKING_TARGETS if getattr(obj, f"{k}_id"))

    def get_target_slug(self, obj) -> str:
        """Slug de la fiche publique : circuit du départ, hôtel de la chambre, sinon l'offre."""
        if obj.tour_departure_id:
            return obj.tour_departure.tour.slug
        if obj.room_id:
            return obj.room.hotel.slug
        return getattr(obj, self.get_kind(obj)).slug


class BookingSerializer(serializers.ModelSerializer):
    """Réservation vue par le client (espace client, lien de suivi)."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    total_amount = MoneyField(amount="total_amount")
    items = BookingItemSerializer(many=True, read_only=True)
    quote_reference = serializers.CharField(
        source="quote.reference", read_only=True, default=None, allow_null=True
    )
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "reference", "status", "status_label", "contact_name", "contact_email",
            "contact_phone", "customer_comments", "expires_at", "total_amount", "items",
            "quote_reference", "can_cancel", "created_at",
        ]

    def get_can_cancel(self, obj) -> bool:
        """Le client peut encore annuler lui-même (avant confirmation)."""
        return obj.status in CUSTOMER_CANCELLABLE


class BookingCreatedSerializer(BookingSerializer):
    """Réponse à la demande : le jeton ouvre la page de suivi (/reservation/<reference>?token=)."""

    access_token = serializers.UUIDField(read_only=True)

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ["access_token"]


class BookingStaffSerializer(BookingSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ["internal_notes", "user_email", "language"]


class BookingDecisionSerializer(serializers.Serializer):
    """Confirmation / refus / annulation : motif ou notes internes facultatifs."""

    reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)
