from django.contrib import admin
from django.db.models import Q
from unfold.decorators import display

from apps.core.admin import (
    CoverPreviewMixin,
    GalleryInline,
    PublishableAdminMixin,
    TranslatedAdmin,
    TranslatedTabularInline,
    amount,
)

from .models import Amenity, Hotel, HotelImage, Residence, ResidenceImage, Room


@admin.register(Amenity)
class AmenityAdmin(TranslatedAdmin):
    list_display = ("name", "icon", "scope")
    list_filter = ("scope",)
    search_fields = ("name",)


class AmenitiesForScopeMixin:
    """Ne propose que les équipements prévus pour ce type d'hébergement."""

    amenity_scope = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "amenities":
            kwargs["queryset"] = Amenity.objects.filter(
                Q(scope=self.amenity_scope) | Q(scope=Amenity.Scope.BOTH)
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class RoomInline(TranslatedTabularInline):
    """Types de chambre ; prix par nuit. Une chambre réservée ne peut pas être supprimée."""

    model = Room
    fields = ("name", "capacity", "quantity", "base_price", "currency", "booking_mode",
              "is_active")
    extra = 0


class HotelImageInline(GalleryInline):
    model = HotelImage


@admin.register(Hotel)
class HotelAdmin(AmenitiesForScopeMixin, CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin):
    amenity_scope = Amenity.Scope.HOTEL
    list_display = ("cover_preview", "name", "destination", "accommodation_type", "stars",
                    "rooms_count", "is_published", "is_featured", "views")
    list_display_links = ("cover_preview", "name")
    list_filter = ("accommodation_type", "stars", "is_published", "is_featured", "destination")
    search_fields = ("name", "address", "destination__name")
    list_select_related = ("destination",)
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("destination",)
    filter_horizontal = ("amenities",)
    readonly_fields = ("views", "created", "updated")
    inlines = (RoomInline, HotelImageInline)
    fieldsets = (
        (None, {"fields": ("name", "slug", "destination", "address", "accommodation_type",
                           "stars", "is_published", "is_featured")}),
        ("Présentation", {"fields": ("short_description", "description", "amenities")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Statistiques", {"fields": ("views", "created", "updated")}),
    )

    @display(description="types de chambre")
    def rooms_count(self, obj):
        return obj.rooms.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("rooms")


class ResidenceImageInline(GalleryInline):
    model = ResidenceImage


@admin.register(Residence)
class ResidenceAdmin(AmenitiesForScopeMixin, CoverPreviewMixin, PublishableAdminMixin,
                     TranslatedAdmin):
    amenity_scope = Amenity.Scope.RESIDENCE
    list_display = ("cover_preview", "name", "destination", "rooms_count", "capacity", "price",
                    "is_published", "is_featured", "views")
    list_display_links = ("cover_preview", "name")
    list_filter = ("is_published", "is_featured", "booking_mode", "destination")
    search_fields = ("name", "address", "destination__name")
    list_select_related = ("destination",)
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("destination",)
    filter_horizontal = ("amenities",)
    readonly_fields = ("views", "created", "updated")
    inlines = (ResidenceImageInline,)
    fieldsets = (
        (None, {"fields": ("name", "slug", "destination", "address", "is_published",
                           "is_featured")}),
        ("Capacité et tarif", {"fields": ("rooms_count", "capacity", "base_price", "currency",
                                          "booking_mode")}),
        ("Présentation", {"fields": ("short_description", "description", "amenities",
                                     "services", "conditions")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Statistiques", {"fields": ("views", "created", "updated")}),
    )

    @display(description="prix / nuit", ordering="base_price")
    def price(self, obj):
        return amount(obj.base_price, obj.currency)
