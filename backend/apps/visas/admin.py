from django.contrib import admin
from unfold.decorators import display

from apps.core.admin import PublishableAdminMixin, TranslatedAdmin, amount

from .models import VisaService


@admin.register(VisaService)
class VisaServiceAdmin(PublishableAdminMixin, TranslatedAdmin):
    list_display = ("destination_country_code", "visa_type", "nationality_code", "purpose",
                    "processing_time", "fees_display", "is_published")
    list_filter = ("purpose", "destination_country_code", "nationality_code", "is_published")
    search_fields = ("visa_type", "destination_country_code", "country_slug")
    fieldsets = (
        (None, {"fields": ("destination_country_code", "country_slug", "nationality_code",
                           "visa_type", "purpose", "is_published")}),
        ("Conditions", {"fields": ("validity_duration", "processing_time", "fees", "currency",
                                   "required_documents", "description")}),
    )

    @display(description="frais", ordering="fees")
    def fees_display(self, obj):
        return amount(obj.fees, obj.currency)
