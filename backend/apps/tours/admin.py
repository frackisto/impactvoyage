from django.contrib import admin
from unfold.admin import TabularInline
from unfold.decorators import display

from apps.core.admin import (
    CoverPreviewMixin,
    GalleryInline,
    PublishableAdminMixin,
    TranslatedAdmin,
    TranslatedStackedInline,
    amount,
)

from .models import Tour, TourDay, TourDeparture, TourImage


class TourImageInline(GalleryInline):
    model = TourImage


class TourDayInline(TranslatedStackedInline):
    """Programme jour par jour."""

    model = TourDay
    verbose_name = "jour"
    verbose_name_plural = "programme jour par jour"
    fields = ("day_number", "title", "description")
    extra = 0
    ordering = ("day_number",)


class TourDepartureInline(TabularInline):
    """
    Départs réservables. Les places réservées sont tenues par les réservations
    (bookings.services) ; un départ déjà réservé ne peut pas être supprimé.
    """

    model = TourDeparture
    fields = ("start_date", "end_date", "capacity", "seats_reserved", "price_override", "status")
    readonly_fields = ("seats_reserved",)
    extra = 0
    ordering = ("start_date",)


@admin.register(Tour)
class TourAdmin(CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin):
    list_display = ("cover_preview", "title", "destination", "scope", "duration_days", "price",
                    "is_published", "is_featured", "views")
    list_display_links = ("cover_preview", "title")
    list_filter = ("scope", "theme", "is_published", "is_featured", "booking_mode", "destination")
    search_fields = ("title", "destination__name")
    list_select_related = ("destination",)
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("destination",)
    filter_horizontal = ("activities",)
    readonly_fields = ("views", "created", "updated")
    inlines = (TourDepartureInline, TourDayInline, TourImageInline)
    fieldsets = (
        (None, {"fields": ("title", "slug", "destination", "scope", "theme", "is_custom",
                           "is_published", "is_featured")}),
        ("Tarif et réservation", {"fields": ("base_price", "currency", "booking_mode",
                                             "duration_days", "min_travelers", "max_travelers")}),
        ("Présentation", {"fields": ("short_description", "description", "activities")}),
        ("Informations pratiques", {"fields": ("departure_points", "transport_info",
                                               "accommodation_info", "inclusions", "exclusions",
                                               "conditions")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Statistiques", {"fields": ("views", "created", "updated")}),
    )

    @display(description="prix", ordering="base_price")
    def price(self, obj):
        return amount(obj.base_price, obj.currency)
