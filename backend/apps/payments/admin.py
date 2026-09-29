"""
Paiements (préparation future, CdC § 37) : consultables, jamais saisis à la
main. Ils seront écrits par les adapters des prestataires quand le paiement
en ligne sera branché.
"""
from django.contrib import admin
from unfold.admin import TabularInline
from unfold.decorators import display

from apps.core.admin import BaseAdmin, amount

from .models import Payment, PaymentStatus, PaymentTransaction

STATUS_LABELS = {
    PaymentStatus.PENDING: "warning",
    PaymentStatus.PAID: "success",
    PaymentStatus.FAILED: "danger",
    PaymentStatus.REFUNDED: "info",
}


class ReadOnlyAdminMixin:
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PaymentTransactionInline(ReadOnlyAdminMixin, TabularInline):
    model = PaymentTransaction
    fields = ("provider", "provider_reference", "status", "created")
    readonly_fields = fields
    extra = 0

    @display(description="créée le")
    def created(self, obj):
        return obj.created_at


@admin.register(Payment)
class PaymentAdmin(ReadOnlyAdminMixin, BaseAdmin):
    list_display = ("booking", "amount_display", "method", "status_label", "created")
    list_filter = ("status", "method")
    search_fields = ("booking__reference", "transactions__provider_reference")
    list_select_related = ("booking",)
    inlines = (PaymentTransactionInline,)

    @display(description="montant", ordering="amount")
    def amount_display(self, obj):
        return amount(obj.amount, obj.currency)

    @display(description="statut", ordering="status", label=STATUS_LABELS)
    def status_label(self, obj):
        return obj.status, obj.get_status_display()
