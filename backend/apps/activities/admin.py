from django.contrib import admin
from unfold.decorators import display

from apps.core.admin import CoverPreviewMixin, GalleryInline, PublishableAdminMixin, TranslatedAdmin, amount

from .models import Activity, ActivityImage


class ActivityImageInline(GalleryInline):
    model = ActivityImage


@admin.register(Activity)
class ActivityAdmin(CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin):
    list_display = ("cover_preview", "title", "destination", "category", "duration_hours",
                    "price", "is_published", "is_featured", "views")
    list_display_links = ("cover_preview", "title")
    list_filter = ("category", "is_published", "is_featured", "destination")
    search_fields = ("title", "destination__name")
    list_select_related = ("destination", "category")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("destination",)
    readonly_fields = ("views", "created", "updated")
    inlines = (ActivityImageInline,)
    fieldsets = (
        (None, {"fields": ("title", "slug", "destination", "category", "is_published",
                           "is_featured")}),
        ("Déroulé et tarif", {"fields": ("duration_hours", "max_participants", "base_price",
                                         "currency", "booking_mode")}),
        ("Présentation", {"fields": ("short_description", "description")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Statistiques", {"fields": ("views", "created", "updated")}),
    )

    @display(description="prix", ordering="base_price")
    def price(self, obj):
        return amount(obj.base_price, obj.currency)
