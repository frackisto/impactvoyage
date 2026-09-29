"""Modération des avis clients (CdC § 20) : approuver, mettre en avant, refuser."""
from django.contrib import admin
from unfold.decorators import action, display

from apps.core.admin import (
    BaseAdmin,
    ServiceManagedAdminMixin,
    image_preview,
    object_status_in,
    run_for_each,
)
from apps.core.exceptions import BusinessError

from . import services
from .models import Review

STATUS_LABELS = {
    Review.Status.EN_ATTENTE: "warning",
    Review.Status.APPROUVE: "success",
    Review.Status.REFUSE: "danger",
}


@admin.register(Review)
class ReviewAdmin(ServiceManagedAdminMixin, BaseAdmin):
    list_display = ("author_name", "stars", "target", "short_comment", "status_label",
                    "is_featured", "created")
    list_filter = ("status", "rating", "is_featured")
    search_fields = ("author_name", "author_email", "comment")
    list_select_related = ("destination", "tour", "hotel", "activity")
    date_hierarchy = "created_at"
    readonly_fields = ("author_name", "author_email", "account", "stars", "comment",
                       "photo_preview", "target", "status", "created")
    fields = ("status", "author_name", "author_email", "account", "stars", "target",
              "comment", "photo_preview", "is_featured", "created")
    actions = ("approve", "approve_and_feature", "reject")
    actions_submit_line = ("approve_submit", "reject_submit")

    @display(description="note", ordering="rating")
    def stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)

    @display(description="sujet")
    def target(self, obj):
        for name in ("destination", "tour", "hotel", "activity"):
            if (related := getattr(obj, name)) is not None:
                return f"{Review._meta.get_field(name).related_model._meta.verbose_name} : {related}"
        return "L'agence"

    @display(description="commentaire")
    def short_comment(self, obj):
        return obj.comment if len(obj.comment) <= 80 else obj.comment[:79] + "…"

    @display(description="compte client")
    def account(self, obj):
        return obj.user or "Sans compte"

    @display(description="photo")
    def photo_preview(self, obj):
        return image_preview(obj.photo, f"Photo de {obj.author_name}", height=160)

    @display(description="statut", ordering="status", label=STATUS_LABELS)
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    def has_add_permission(self, request):
        return False  # déposés par les clients sur le site

    def _can_move_to(self, request, object_id, status):
        others = set(Review.Status.values) - {status}
        return object_status_in(self, request, object_id, others)

    def has_approve_permission(self, request, object_id=None):
        return self._can_move_to(request, object_id, Review.Status.APPROUVE)

    def has_reject_permission(self, request, object_id=None):
        return self._can_move_to(request, object_id, Review.Status.REFUSE)

    @admin.action(description="Approuver", permissions=["change"])
    def approve(self, request, queryset):
        run_for_each(self, request, queryset, services.approve_review, "avis approuvé(s)")

    @admin.action(description="Approuver et afficher sur l'accueil", permissions=["change"])
    def approve_and_feature(self, request, queryset):
        def feature(review):
            if review.status == Review.Status.APPROUVE:  # déjà publié : mise en avant seule
                review.is_featured = True
                review.save(update_fields=["is_featured", "updated_at"])
            else:
                services.approve_review(review, featured=True)

        run_for_each(self, request, queryset, feature, "avis approuvé(s) et mis en avant")

    @admin.action(description="Refuser", permissions=["change"])
    def reject(self, request, queryset):
        run_for_each(self, request, queryset, services.reject_review, "avis refusé(s)")

    def _moderate(self, request, service, obj, success):
        try:
            service(obj)
        except BusinessError as exc:
            self.message_user(request, exc.message, level="error")
        else:
            self.message_user(request, success, level="success")

    @action(description="Approuver", permissions=["approve"])
    def approve_submit(self, request, obj):
        self._moderate(request, lambda r: services.approve_review(r, featured=r.is_featured),
                       obj, "Avis approuvé : il est publié sur le site.")

    @action(description="Refuser", permissions=["reject"])
    def reject_submit(self, request, obj):
        self._moderate(request, services.reject_review, obj, "Avis refusé.")
