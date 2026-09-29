"""
Notifications du backoffice (CdC § 30) : chaque membre de l'équipe ne voit
que les siennes. « Ouvrir » les marque comme lues et mène à la fiche concernée.
"""
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from unfold.decorators import action, display

from apps.core.admin import BaseAdmin, list_decision_view

from . import services
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(BaseAdmin):
    list_display = ("title", "event", "read_label", "created", "open_link")
    list_filter = ("is_read", "event")
    search_fields = ("title", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("event", "title", "message", "open_link", "read_label", "read_at",
                       "created")
    fields = readonly_fields
    actions = ("mark_read",)
    actions_list = ("mark_all_read",)
    actions_detail = ("open_detail",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(recipient=request.user)

    # --- Droits : ses propres notifications, pour tout membre de l'équipe ---

    def _is_team_member(self, request):
        return request.user.is_active and request.user.is_staff

    def has_module_permission(self, request):
        return self._is_team_member(request)

    def has_view_permission(self, request, obj=None):
        return self._is_team_member(request) and (obj is None or obj.recipient_id == request.user.pk)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_read_permission(self, request, object_id=None):
        return self._is_team_member(request)

    # --- Colonnes ---

    @display(description="état", label={True: "default", False: "info"})
    def read_label(self, obj):
        return obj.is_read, "Lue" if obj.is_read else "Non lue"

    @display(description="")
    def open_link(self, obj):
        url = reverse("admin:notifications_notification_open_detail", args=[obj.pk])
        return format_html('<a href="{}" class="text-primary-600">Ouvrir</a>', url)

    # --- Actions ---

    @admin.action(description="Marquer comme lues", permissions=["read"])
    def mark_read(self, request, queryset):
        for notification in queryset.filter(is_read=False):
            services.mark_as_read(notification)
        self.message_user(request, "Notifications marquées comme lues.", messages.SUCCESS)

    @action(description="Tout marquer comme lu", url_path="mark-all-read", permissions=["read"],
            icon="done_all")
    def mark_all_read(self, request):
        def perform():
            count = services.mark_all_as_read(request.user)
            return messages.SUCCESS, f"{count} notification(s) marquée(s) comme lue(s)."

        return list_decision_view(
            self, request,
            title="Tout marquer comme lu",
            description="Toutes vos notifications non lues seront marquées comme lues.",
            submit_label="Tout marquer comme lu",
            perform=perform,
        )

    @action(description="Ouvrir la fiche", url_path="open", permissions=["read"],
            icon="open_in_new")
    def open_detail(self, request, object_id):
        # Marquer sa propre notification comme lue en l'ouvrant est sans risque (GET).
        notification = self.get_queryset(request).filter(pk=object_id).first()
        if notification is None:
            return redirect(reverse("admin:notifications_notification_changelist"))
        services.mark_as_read(notification)
        link = notification.link
        if link and url_has_allowed_host_and_scheme(link, allowed_hosts={request.get_host()}):
            return redirect(link)
        return redirect(reverse("admin:notifications_notification_change", args=[notification.pk]))
