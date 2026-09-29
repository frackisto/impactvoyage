from django.contrib import admin
from unfold.decorators import display

from apps.core.admin import CoverPreviewMixin, GalleryInline, PublishableAdminMixin, TranslatedAdmin, amount

from .models import Vehicle, VehicleImage


class VehicleImageInline(GalleryInline):
    model = VehicleImage


@admin.register(Vehicle)
class VehicleAdmin(CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin):
    list_display = ("cover_preview", "name", "plate_number", "category", "seats", "transmission",
                    "price", "is_published", "is_featured", "views")
    list_display_links = ("cover_preview", "name")
    list_filter = ("category", "transmission", "fuel", "is_published", "is_featured")
    search_fields = ("brand", "model", "plate_number")
    prepopulated_fields = {"slug": ("brand", "model")}
    readonly_fields = ("views", "created", "updated")
    inlines = (VehicleImageInline,)
    fieldsets = (
        (None, {"fields": ("brand", "model", "slug", "category", "year", "plate_number",
                           "is_published", "is_featured")}),
        ("Caractéristiques", {"fields": ("seats", "transmission", "fuel", "air_conditioning",
                                         "features", "description")}),
        ("Tarif et réservation", {"fields": ("base_price", "currency", "booking_mode")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Statistiques", {"fields": ("views", "created", "updated")}),
    )

    @display(description="véhicule", ordering="brand")
    def name(self, obj):
        return f"{obj.brand} {obj.model}"

    @display(description="prix / jour", ordering="base_price")
    def price(self, obj):
        return amount(obj.base_price, obj.currency)
