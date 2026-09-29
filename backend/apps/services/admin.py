from django.contrib import admin

from apps.core.admin import PublishableAdminMixin, TranslatedAdmin, TranslatedTabularInline

from .models import Service, ServicePrice


class ServicePriceInline(TranslatedTabularInline):
    model = ServicePrice
    fields = ("label", "price", "currency", "unit", "order")
    extra = 0


@admin.register(Service)
class ServiceAdmin(PublishableAdminMixin, TranslatedAdmin):
    list_display = ("title", "quote_service_type", "order", "is_published")
    list_editable = ("order",)
    list_filter = ("is_published",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = (ServicePriceInline,)
    fields = ("title", "slug", "short_description", "description", "icon", "order",
              "quote_service_type", "is_published")
