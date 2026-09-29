"""
Traitement des devis et des messages de contact dans le backoffice (Phase 19).

Devis : assignation d'un commercial (le devis nouveau passe « En cours »),
envoi de la proposition chiffrée avec le lien client, refus, clôture ; tout
passe par inquiries.services. Messages : marqués lus à l'ouverture, puis
traités ou archivés.
"""
from datetime import timedelta

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from unfold.decorators import action, display
from unfold.widgets import UnfoldAdminDecimalFieldWidget, UnfoldAdminTextareaWidget

from apps.core.admin import (
    BaseAdmin,
    DateRangeFilter,
    ServiceManagedAdminMixin,
    SoftDeleteAdminMixin,
    amount,
    date_input,
    decision_view,
    object_status_in,
    run_for_each,
)
from apps.core.choices import RequestedService
from apps.core.exceptions import BusinessError

from . import services
from .models import ContactMessage, QuoteRequest

QStatus = QuoteRequest.Status
CStatus = ContactMessage.Status

QUOTE_LABELS = {
    QStatus.NOUVELLE: "info",
    QStatus.EN_COURS: "warning",
    QStatus.DEVIS_ENVOYE: "primary",
    QStatus.ACCEPTEE: "success",
    QStatus.REFUSEE: "danger",
    QStatus.TERMINEE: "default",
}
CONTACT_LABELS = {
    CStatus.NOUVEAU: "info",
    CStatus.LU: "warning",
    CStatus.TRAITE: "success",
    CStatus.ARCHIVE: "default",
}


def _quote_statuses_allowing(target):
    return {s for s, targets in services.QUOTE_TRANSITIONS.items() if target in targets}


CAN_SEND_PROPOSAL = _quote_statuses_allowing(QStatus.DEVIS_ENVOYE)
CAN_REFUSE = _quote_statuses_allowing(QStatus.REFUSEE)
CAN_CLOSE = _quote_statuses_allowing(QStatus.TERMINEE)
OPEN_STATUSES = {QStatus.NOUVELLE, QStatus.EN_COURS, QStatus.DEVIS_ENVOYE}


class ProposalForm(forms.Form):
    amount = forms.DecimalField(
        label="Montant proposé", min_value=0, max_digits=12, decimal_places=2,
        widget=UnfoldAdminDecimalFieldWidget,
    )
    valid_until = forms.DateField(label="Proposition valable jusqu'au", widget=date_input())
    message = forms.CharField(
        label="Message au client",
        help_text="Programme, prestations incluses, conditions. Envoyé par email avec le "
                  "lien qui permet au client d'accepter ou de refuser.",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 10}),
    )

    def clean_valid_until(self):
        valid_until = self.cleaned_data["valid_until"]
        if valid_until < timezone.localdate():
            raise forms.ValidationError("La date de validité est déjà passée.")
        return valid_until


@admin.register(QuoteRequest)
class QuoteRequestAdmin(ServiceManagedAdminMixin, SoftDeleteAdminMixin, BaseAdmin):
    list_display = ("reference", "client", "destination_label", "date_departure", "travelers",
                    "status_label", "assigned_to", "created")
    list_filter = ("status", "travel_type", "assigned_to", ("created_at", DateRangeFilter))
    list_filter_submit = True
    search_fields = ("reference", "first_name", "last_name", "email", "phone",
                     "destination_text", "destination__name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("destination", "assigned_to")
    actions = ("assign_to_me", "refuse_selected", "close_selected")
    actions_detail = ("send_proposal_detail",)
    actions_submit_line = ("assign_to_me_submit", "refuse_submit", "close_submit")
    fields_readonly_request = (
        "reference", "status", "created", "origin", "language", "consent_at",
        "first_name", "last_name", "email", "phone", "whatsapp", "country_code",
        "destination_label", "date_departure", "date_return", "adults", "children",
        "travel_type", "budget_display", "accommodation_pref", "transport_pref",
        "activities_display", "services_display", "comments",
        "proposal_display", "proposal_message", "proposal_sent_at", "proposal_valid_until",
        "booking_link", "tracking_link",
    )
    readonly_fields = fields_readonly_request
    fieldsets = (
        ("Demande", {"fields": ("reference", "status", "created", "origin",
                                "language", "consent_at")}),
        ("Client", {"fields": ("first_name", "last_name", "email", "phone", "whatsapp",
                               "country_code")}),
        ("Projet de voyage", {"fields": ("destination_label", "date_departure", "date_return",
                                         "adults", "children", "travel_type", "budget_display",
                                         "accommodation_pref", "transport_pref",
                                         "activities_display", "services_display", "comments")}),
        ("Traitement", {"fields": ("assigned_to", "proposal_display", "proposal_message",
                                   "proposal_sent_at", "proposal_valid_until", "booking_link",
                                   "tracking_link")}),
    )

    def get_queryset(self, request):
        return (super().get_queryset(request)
                .select_related("destination", "assigned_to", "source_tour", "source_offer")
                .prefetch_related("activities"))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            from django.contrib.auth import get_user_model

            kwargs["queryset"] = get_user_model().objects.filter(is_staff=True, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # --- Colonnes ---

    @display(description="client", ordering="last_name")
    def client(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @display(description="destination")
    def destination_label(self, obj):
        return obj.destination_text or (obj.destination.name if obj.destination else "—")

    @display(description="voyageurs")
    def travelers(self, obj):
        return obj.adults + obj.children

    @display(description="statut", ordering="status", label=QUOTE_LABELS)
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @display(description="budget")
    def budget_display(self, obj):
        return amount(obj.budget, obj.currency)

    @display(description="origine")
    def origin(self, obj):
        if obj.source_tour_id:
            return f"Fiche circuit : {obj.source_tour}"
        if obj.source_offer_id:
            return f"Offre : {obj.source_offer}"
        return "Formulaire de devis"

    @display(description="activités souhaitées")
    def activities_display(self, obj):
        return ", ".join(str(a) for a in obj.activities.all()) or "—"

    @display(description="services demandés")
    def services_display(self, obj):
        labels = dict(RequestedService.choices)
        return ", ".join(labels.get(s, s) for s in obj.services_requested) or "—"

    @display(description="montant proposé")
    def proposal_display(self, obj):
        return amount(obj.proposal_amount, obj.currency)

    @display(description="réservation créée")
    def booking_link(self, obj):
        booking = getattr(obj, "booking", None)
        if booking is None:
            return "—"
        url = reverse("admin:bookings_booking_change", args=[booking.pk])
        return format_html('<a href="{}" class="text-primary-600">{}</a>', url, booking.reference)

    @display(description="lien de suivi du client")
    def tracking_link(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener" class="text-primary-600">'
                           "Ouvrir la page de suivi</a>", services.client_quote_url(obj))

    # --- Droits ---

    def has_add_permission(self, request):
        # Les demandes arrivent du site (consentement du client obligatoire).
        return False

    def has_send_proposal_permission(self, request, object_id=None):
        return object_status_in(self, request, object_id, CAN_SEND_PROPOSAL)

    def has_refuse_permission(self, request, object_id=None):
        return object_status_in(self, request, object_id, CAN_REFUSE)

    def has_close_permission(self, request, object_id=None):
        return object_status_in(self, request, object_id, CAN_CLOSE)

    def has_assign_me_permission(self, request, object_id=None):
        if not object_status_in(self, request, object_id, OPEN_STATUSES):
            return False
        return object_id is None or not QuoteRequest.objects.filter(
            pk=object_id, assigned_to=request.user).exists()

    # --- Enregistrement ---

    def save_model(self, request, obj, form, change):
        if change and "assigned_to" in form.changed_data and obj.assigned_to is not None:
            # Par le service : un devis nouveau passe « En cours » au passage.
            self._call(request, services.assign_quote, obj, obj.assigned_to)
            form.changed_data.remove("assigned_to")
        super().save_model(request, obj, form, change)

    def _call(self, request, service, *args, success=None):
        try:
            service(*args)
        except BusinessError as exc:
            self.message_user(request, exc.message, level="error")
            return False
        if success:
            self.message_user(request, success, level="success")
        return True

    # --- Actions groupées ---

    @admin.action(description="M'assigner les devis sélectionnés", permissions=["change"])
    def assign_to_me(self, request, queryset):
        run_for_each(self, request, queryset.filter(status__in=OPEN_STATUSES),
                     lambda q: services.assign_quote(q, request.user), "devis assigné(s)")

    @admin.action(description="Refuser les devis sélectionnés", permissions=["change"])
    def refuse_selected(self, request, queryset):
        run_for_each(self, request, queryset,
                     lambda q: services.change_quote_status(q, QStatus.REFUSEE), "devis refusé(s)")

    @admin.action(description="Clôturer les devis sélectionnés", permissions=["change"])
    def close_selected(self, request, queryset):
        run_for_each(self, request, queryset,
                     lambda q: services.change_quote_status(q, QStatus.TERMINEE),
                     "devis clôturé(s)")

    # --- Boutons de la fiche ---

    @action(description="M'assigner ce devis", permissions=["assign_me"])
    def assign_to_me_submit(self, request, obj):
        self._call(request, services.assign_quote, obj, request.user,
                   success=f"Devis {obj.reference} assigné à {request.user}.")

    @action(description="Refuser le devis", permissions=["refuse"])
    def refuse_submit(self, request, obj):
        self._call(request, services.change_quote_status, obj, QStatus.REFUSEE,
                   success=f"Devis {obj.reference} refusé.")

    @action(description="Clôturer le devis", permissions=["close"])
    def close_submit(self, request, obj):
        self._call(request, services.change_quote_status, obj, QStatus.TERMINEE,
                   success=f"Devis {obj.reference} clôturé.")

    @action(description="Envoyer la proposition", url_path="send-proposal",
            permissions=["send_proposal"], icon="send")
    def send_proposal_detail(self, request, object_id):
        quote = self.get_object(request, object_id)
        initial, summary = {}, ()
        if quote is not None:
            initial = {
                "amount": quote.proposal_amount,
                "message": quote.proposal_message,
                "valid_until": quote.proposal_valid_until
                or timezone.localdate() + timedelta(days=14),
            }
            summary = [
                ("Client", f"{quote.first_name} {quote.last_name} — {quote.email}"),
                ("Destination", self.destination_label(quote)),
                ("Dates", " → ".join(filter(None, [
                    quote.date_departure and f"{quote.date_departure:%d/%m/%Y}",
                    quote.date_return and f"{quote.date_return:%d/%m/%Y}",
                ])) or "—"),
                ("Voyageurs", f"{quote.adults} adulte(s), {quote.children} enfant(s)"),
                ("Budget", self.budget_display(quote)),
                ("Services", self.services_display(quote)),
            ]

        def perform(obj, data):
            services.send_proposal(obj, amount=data["amount"], message=data["message"],
                                   valid_until=data["valid_until"], by=request.user)
            return f"Proposition envoyée à {obj.email}."

        resend = quote is not None and quote.status == QStatus.DEVIS_ENVOYE
        return decision_view(
            self, request, object_id,
            title=f"{'Renvoyer' if resend else 'Envoyer'} la proposition "
                  f"{quote.reference if quote else ''}".strip(),
            description="Le client reçoit la proposition par email, avec un lien pour "
                        "l'accepter (une réservation est alors créée) ou la refuser.",
            submit_label="Envoyer au client",
            form_class=ProposalForm,
            initial=initial,
            summary=summary,
            perform=perform,
        )


@admin.register(ContactMessage)
class ContactMessageAdmin(ServiceManagedAdminMixin, BaseAdmin):
    list_display = ("subject", "name", "email", "status_label", "created")
    list_filter = ("status", ("created_at", DateRangeFilter))
    list_filter_submit = True
    search_fields = ("name", "email", "subject", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("name", "email", "reply_link", "phone", "subject", "message",
                       "status", "created")
    fields = readonly_fields
    actions = ("mark_treated", "archive")
    actions_submit_line = ("mark_treated_submit", "archive_submit")

    @display(description="statut", ordering="status", label=CONTACT_LABELS)
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @display(description="répondre")
    def reply_link(self, obj):
        return format_html('<a href="mailto:{}?subject={}" class="text-primary-600">'
                           "Répondre par email</a>", obj.email, f"Re: {obj.subject}")

    def has_add_permission(self, request):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Ouvrir un message nouveau le marque comme lu (pour qui peut le traiter).
        if request.method == "GET" and object_status_in(self, request, object_id, {CStatus.NOUVEAU}):
            services.change_contact_status(ContactMessage.objects.get(pk=object_id), CStatus.LU)
        return super().change_view(request, object_id, form_url, extra_context)

    def _can_move_to(self, request, object_id, target):
        allowed = {s for s, targets in services.CONTACT_TRANSITIONS.items() if target in targets}
        return object_status_in(self, request, object_id, allowed)

    def has_treat_permission(self, request, object_id=None):
        return self._can_move_to(request, object_id, CStatus.TRAITE)

    def has_archive_permission(self, request, object_id=None):
        return self._can_move_to(request, object_id, CStatus.ARCHIVE)

    def _change(self, request, obj, status, success):
        try:
            services.change_contact_status(obj, status)
        except BusinessError as exc:
            self.message_user(request, exc.message, level="error")
        else:
            self.message_user(request, success, level="success")

    @admin.action(description="Marquer comme traités", permissions=["change"])
    def mark_treated(self, request, queryset):
        run_for_each(self, request, queryset,
                     lambda m: services.change_contact_status(m, CStatus.TRAITE),
                     "message(s) traité(s)")

    @admin.action(description="Archiver", permissions=["change"])
    def archive(self, request, queryset):
        run_for_each(self, request, queryset,
                     lambda m: services.change_contact_status(m, CStatus.ARCHIVE),
                     "message(s) archivé(s)")

    @action(description="Marquer comme traité", permissions=["treat"])
    def mark_treated_submit(self, request, obj):
        self._change(request, obj, CStatus.TRAITE, "Message marqué comme traité.")

    @action(description="Archiver", permissions=["archive"])
    def archive_submit(self, request, obj):
        self._change(request, obj, CStatus.ARCHIVE, "Message archivé.")
