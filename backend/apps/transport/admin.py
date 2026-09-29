from django.contrib import admin
from unfold.decorators import display

from apps.core.admin import CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin, amount

from .models import TransportService


@admin.register(TransportService)
class TransportServiceAdmin(CoverPreviewMixin, PublishableAdminMixin, TranslatedAdmin):
    list_display = ("cover_preview", "title", "transport_type", "origin", "destination",
                    "max_passengers", "price", "is_published")
    list_display_links = ("cover_preview", "title")
    list_filter = ("transport_type", "is_published")
    search_fields = ("title", "origin", "destination")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "transport_type", "origin", "destination",
                           "is_published")}),
        ("Tarif et capacité", {"fields": ("max_passengers", "price_from", "currency",
                                          "schedule_info")}),
        ("Présentation", {"fields": ("description",)}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
    )

    @display(description="à partir de", ordering="price_from")
    def price(self, obj):
        return amount(obj.price_from, obj.currency)
