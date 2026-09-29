from django import forms
from django.contrib import admin
from django.utils import timezone
from unfold.decorators import display

from apps.core.admin import CoverPreviewMixin, TranslatedAdmin, amount
from apps.core.revalidation import revalidate_model

from .models import OFFER_TARGETS, Offer


class OfferForm(forms.ModelForm):
    """Messages clairs pour les contraintes de la base (prix, dates, cible unique)."""

    def clean(self):
        data = super().clean()
        initial, promo = data.get("initial_price"), data.get("promo_price")
        if initial is not None and promo is not None and promo >= initial:
            self.add_error("promo_price", "Le prix promotionnel doit être inférieur au prix initial.")
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "La fin de l'offre doit suivre son début.")
        targets = [name for name in OFFER_TARGETS if data.get(name)]
        if len(targets) > 1:
            raise forms.ValidationError(
                "Une offre cible au plus une fiche (circuit, hôtel, résidence, véhicule ou activité)."
            )
        return data


@admin.register(Offer)
class OfferAdmin(CoverPreviewMixin, TranslatedAdmin):
    form = OfferForm
    list_display = ("cover_preview", "title", "offer_type", "prices", "discount", "start_date",
                    "end_date", "seats_available", "is_active", "is_running")
    list_display_links = ("cover_preview", "title")
    list_filter = ("offer_type", "is_active", "badge")
    search_fields = ("title",)
    date_hierarchy = "start_date"
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("destination", "tour", "hotel", "residence", "vehicle", "activity")
    readonly_fields = ("created", "updated")
    actions = ("activate", "deactivate")
    fieldsets = (
        (None, {"fields": ("title", "slug", "offer_type", "badge", "is_active")}),
        ("Prix et validité", {"fields": ("initial_price", "promo_price", "currency",
                                         "start_date", "end_date", "seats_available")}),
        ("Cible (au plus une)", {"fields": ("destination", "tour", "hotel", "residence",
                                            "vehicle", "activity")}),
        ("Présentation", {"fields": ("short_description", "description", "conditions")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
    )

    @display(description="prix")
    def prices(self, obj):
        return f"{amount(obj.promo_price, obj.currency)} (au lieu de {amount(obj.initial_price, obj.currency)})"

    @display(description="réduction")
    def discount(self, obj):
        return f"-{obj.discount_percent} %"

    @display(description="en cours", boolean=True)
    def is_running(self, obj):
        return obj.is_active and obj.start_date <= timezone.localdate() <= obj.end_date

    @admin.action(description="Activer la sélection", permissions=["change"])
    def activate(self, request, queryset):
        count = queryset.update(is_active=True)
        revalidate_model(Offer)
        self.message_user(request, f"{count} offre(s) activée(s).")

    @admin.action(description="Désactiver la sélection", permissions=["change"])
    def deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        revalidate_model(Offer)
        self.message_user(request, f"{count} offre(s) désactivée(s).")
