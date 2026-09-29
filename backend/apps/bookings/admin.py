"""
Traitement des réservations dans le backoffice (Phase 19) : confirmation,
refus et annulation passent par bookings.services (stock réservé ou libéré
sous verrou, email au client). La fiche est en lecture seule, sauf les notes
internes ; une réservation qui bloque du stock ne peut pas être supprimée.
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import TabularInline
from unfold.decorators import action, display

from apps.core.admin import (
    BaseAdmin,
    DateRangeFilter,
    ReasonForm,
    ServiceManagedAdminMixin,
    SoftDeleteAdminMixin,
    amount,
    decision_view,
    object_status_in,
)

from . import services
from .models import Booking, BookingItem

Status = Booking.Status

STATUS_LABELS = {
    Status.REQUESTED: "info",
    Status.PENDING: "warning",
    Status.CONFIRMED: "success",
    Status.COMPLETED: "primary",
    Status.CANCELLED: "danger",
    Status.REJECTED: "danger",
    Status.EXPIRED: "danger",
}


def _statuses_allowing(target):
    return {status for status, targets in services.ALLOWED_TRANSITIONS.items() if target in targets}


CAN_CONFIRM = _statuses_allowing(Status.CONFIRMED)
CAN_REJECT = _statuses_allowing(Status.REJECTED)
CAN_CANCEL = _statuses_allowing(Status.CANCELLED)


class ConfirmForm(ReasonForm):
    """Confirmation : les notes internes peuvent être complétées au passage."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].label = "Notes internes"


class BookingItemInline(TabularInline):
    """Prestations réservées : prix figés à la demande, jamais modifiés ici."""

    model = BookingItem
    fields = ("label", "start_date", "end_date", "quantity", "unit", "line_amount",
              "pickup_location", "dropoff_location", "is_blocking")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = False

    @display(description="prix unitaire")
    def unit(self, obj):
        return amount(obj.unit_price, obj.booking.currency)

    @display(description="total ligne")
    def line_amount(self, obj):
        return amount(obj.line_total, obj.booking.currency)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(ServiceManagedAdminMixin, SoftDeleteAdminMixin, BaseAdmin):
    list_display = ("reference", "contact_name", "status_label", "first_date", "total",
                    "created", "expires_at")
    list_filter = ("status", ("created_at", DateRangeFilter), "currency")
    list_filter_submit = True
    search_fields = ("reference", "contact_name", "contact_email", "contact_phone",
                     "items__label")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = (BookingItemInline,)
    actions_detail = ("confirm_detail", "reject_detail", "cancel_detail")
    fieldsets = (
        ("Réservation", {"fields": ("reference", "status", "total", "expires_at",
                                    "created", "updated", "quote_link", "tracking_link")}),
        ("Client", {"fields": ("contact_name", "contact_email", "contact_phone", "account",
                               "language", "consent_at", "customer_comments")}),
        ("Suivi par l'agence", {"fields": ("internal_notes",)}),
    )
    readonly_fields = ("reference", "status", "total", "expires_at", "created",
                       "updated", "quote_link", "tracking_link", "contact_name",
                       "contact_email", "contact_phone", "account", "language", "consent_at",
                       "customer_comments")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "quote").prefetch_related("items")

    # --- Colonnes ---

    @display(description="statut", ordering="status", label=STATUS_LABELS)
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @display(description="total", ordering="total_amount")
    def total(self, obj):
        return amount(obj.total_amount, obj.currency)

    @display(description="début")
    def first_date(self, obj):
        dates = [item.start_date for item in obj.items.all()]
        return min(dates) if dates else "—"

    @display(description="compte client")
    def account(self, obj):
        return obj.user or "Sans compte (lien de suivi)"

    @display(description="devis d'origine")
    def quote_link(self, obj):
        if not obj.quote_id:
            return "—"
        url = reverse("admin:inquiries_quoterequest_change", args=[obj.quote_id])
        return format_html('<a href="{}" class="text-primary-600">{}</a>', url, obj.quote.reference)

    @display(description="lien de suivi du client")
    def tracking_link(self, obj):
        url = services.client_booking_url(obj)
        return format_html('<a href="{}" target="_blank" rel="noopener" class="text-primary-600">'
                           "Ouvrir la page de suivi</a>", url)

    # --- Droits ---

    def has_add_permission(self, request):
        # Les réservations naissent sur le site (demande) ou d'un devis accepté.
        return False

    def has_delete_permission(self, request, obj=None):
        # Annuler d'abord, pour libérer le stock. Vérifié aussi objet par objet
        # par la suppression groupée de Django, qui refuse alors toute la sélection.
        if obj is not None and obj.status in Booking.BLOCKING_STATUSES:
            return False
        return super().has_delete_permission(request, obj)

    def has_confirm_permission(self, request, object_id=None):
        return object_status_in(self, request, object_id, CAN_CONFIRM)

    def has_reject_permission(self, request, object_id=None):
        return object_status_in(self, request, object_id, CAN_REJECT)

    def has_cancel_permission(self, request, object_id=None):
        return object_status_in(self, request, object_id, CAN_CANCEL)

    # --- Décisions ---

    def _summary(self, booking):
        lines = [(item.label, amount(item.line_total, booking.currency))
                 for item in booking.items.all()]
        return [("Client", f"{booking.contact_name} — {booking.contact_email}"),
                ("Statut", booking.get_status_display()),
                *lines,
                ("Total", amount(booking.total_amount, booking.currency))]

    @action(description="Confirmer", url_path="confirm", permissions=["confirm"],
            icon="check_circle")
    def confirm_detail(self, request, object_id):
        booking = self.get_object(request, object_id)

        def perform(obj, data):
            services.confirm_booking(obj, internal_notes=data["reason"] or None)
            return f"Réservation {obj.reference} confirmée ; le client a été prévenu par email."

        return decision_view(
            self, request, object_id,
            title=f"Confirmer la réservation {booking.reference}" if booking else "Confirmer",
            description="Le stock (places, véhicule, chambres) est réservé et le client reçoit "
                        "un email de confirmation.",
            submit_label="Confirmer la réservation",
            form_class=ConfirmForm,
            initial={"reason": booking.internal_notes if booking else ""},
            summary=self._summary(booking) if booking else (),
            perform=perform,
        )

    @action(description="Refuser", url_path="reject", permissions=["reject"], icon="block")
    def reject_detail(self, request, object_id):
        booking = self.get_object(request, object_id)

        def perform(obj, data):
            services.reject_booking(obj, reason=data["reason"])
            return f"Demande {obj.reference} refusée ; le client a été prévenu par email."

        return decision_view(
            self, request, object_id,
            title=f"Refuser la demande {booking.reference}" if booking else "Refuser",
            description="Le motif est ajouté aux notes internes et envoyé au client.",
            submit_label="Refuser la demande",
            form_class=ReasonForm,
            summary=self._summary(booking) if booking else (),
            perform=perform,
        )

    @action(description="Annuler", url_path="cancel", permissions=["cancel"], icon="cancel")
    def cancel_detail(self, request, object_id):
        booking = self.get_object(request, object_id)

        def perform(obj, data):
            services.cancel_booking(obj, reason=data["reason"])
            return f"Réservation {obj.reference} annulée ; le stock est libéré."

        return decision_view(
            self, request, object_id,
            title=f"Annuler la réservation {booking.reference}" if booking else "Annuler",
            description="Le stock réservé est libéré et le client reçoit un email d'annulation. "
                        "Le motif est ajouté aux notes internes.",
            submit_label="Annuler la réservation",
            form_class=ReasonForm,
            summary=self._summary(booking) if booking else (),
            perform=perform,
        )

