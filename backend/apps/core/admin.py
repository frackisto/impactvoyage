"""
Socle du backoffice (Phase 19, architecture § 13) et administration des
réglages transverses : catégories, tags, paramètres du site, taux de change.

Règles communes :
- les changements de statut passent par les services métier, jamais par un
  champ éditable ; une erreur métier devient un message dans l'admin ;
- toute action qui modifie des données passe par un formulaire POST (page de
  décision), jamais par un simple lien ;
- les contenus traduits affichent un champ par langue (titre [fr], titre [en]).
"""
from django import forms
from django.contrib import admin, messages
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from modeltranslation.admin import (
    TranslationAdmin,
    TranslationStackedInline,
    TranslationTabularInline,
)
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import action, display
from unfold.overrides import FORMFIELD_OVERRIDES_INLINE
from unfold.widgets import INPUT_CLASSES, UnfoldAdminTextareaWidget

from .exceptions import BusinessError
from .formatting import format_amount
from .models import Category, ExchangeRate, SiteSettings, Tag
from .revalidation import revalidate_model
from .services import RATES_CACHE_KEY, update_exchange_rates

# --- Classes de base ----------------------------------------------------------


# Une URL saisie sans schéma devient https:// (comportement par défaut de Django 6).
HTTPS_URLS = {models.URLField: {"assume_scheme": "https"}}
INLINE_OVERRIDES = {
    **FORMFIELD_OVERRIDES_INLINE,
    models.URLField: {**FORMFIELD_OVERRIDES_INLINE[models.URLField], "assume_scheme": "https"},
}


class BaseAdmin(ModelAdmin):
    list_per_page = 25
    warn_unsaved_form = True
    formfield_overrides = HTTPS_URLS  # complété par les widgets unfold

    # Libellés français des dates de TimeStampedModel (champs sans verbose_name ;
    # leur en donner un imposerait une migration par app).
    @display(description="créé le", ordering="created_at")
    def created(self, obj):
        return local_datetime(obj.created_at)

    @display(description="modifié le", ordering="updated_at")
    def updated(self, obj):
        return local_datetime(obj.updated_at)

    @display(description="vues", ordering="views")
    def views(self, obj):
        return obj.view_count


class DateRangeFilter(RangeDateFilter):
    """Filtre par période sur created_at, avec un titre en français."""

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = "date de réception"


class TranslatedAdmin(BaseAdmin, TranslationAdmin):
    """Contenu traduit : chaque champ traduit apparaît une fois par langue."""


class TranslatedTabularInline(TabularInline, TranslationTabularInline):
    formfield_overrides = INLINE_OVERRIDES


class TranslatedStackedInline(StackedInline, TranslationStackedInline):
    formfield_overrides = INLINE_OVERRIDES


def local_datetime(value):
    """Date et heure lisibles (« 29 septembre 2026 08:24 ») pour une colonne calculée."""
    return date_format(timezone.localtime(value), "DATETIME_FORMAT") if value else "—"


def object_status_in(model_admin, request, object_id, statuses):
    """
    Droit d'une décision (action unfold) : droit de modification, et statut de
    l'objet compatible. Sans object_id (liste des actions), seul le droit compte.
    """
    if not model_admin.has_change_permission(request):
        return False
    if object_id is None:
        return True
    try:
        return model_admin.model._default_manager.filter(pk=object_id, status__in=statuses).exists()
    except (ValueError, ValidationError):  # identifiant mal formé dans l'URL
        return False


def image_preview(file, alt="", height=64):
    if not file:
        return "—"
    return format_html(
        '<img src="{}" alt="{}" style="height:{}px;width:auto;border-radius:6px">',
        file.url, alt, height,
    )


def amount(value, currency):
    return "—" if value is None else format_amount(value, currency)


class GalleryInline(TranslatedTabularInline):
    """Galerie photo d'un contenu (GalleryImage) : aperçu, fichier, texte alternatif, ordre."""

    fields = ("preview", "image", "alt_text", "order")
    verbose_name = "photo"
    verbose_name_plural = "galerie photo"
    readonly_fields = ("preview",)
    extra = 0

    @display(description="aperçu")
    def preview(self, obj):
        return image_preview(obj.image, obj.alt_text)


class MediaAssetInline(TranslatedTabularInline):
    """Galerie mixte (MediaAsset) : photo ou lien vidéo YouTube / Vimeo."""

    fields = ("preview", "type", "image", "video_url", "alt_text", "order")
    verbose_name = "média"
    verbose_name_plural = "galerie (photos et vidéos)"
    readonly_fields = ("preview",)
    extra = 0

    @display(description="aperçu")
    def preview(self, obj):
        return image_preview(obj.image, obj.alt_text) if obj.image else (obj.video_url or "—")


class CoverPreviewMixin:
    @display(description="image")
    def cover_preview(self, obj):
        return image_preview(obj.cover_image, obj.cover_alt, height=40)


class PublishableAdminMixin:
    """Publication / dépublication groupée (PublishableMixin.is_published)."""

    actions = ("publish", "unpublish")

    @admin.action(description="Publier la sélection", permissions=["change"])
    def publish(self, request, queryset):
        count = queryset.update(is_published=True)
        revalidate_model(queryset.model)
        self.message_user(request, f"{count} élément(s) publié(s).", messages.SUCCESS)

    @admin.action(description="Dépublier la sélection", permissions=["change"])
    def unpublish(self, request, queryset):
        count = queryset.update(is_published=False)
        revalidate_model(queryset.model)
        self.message_user(request, f"{count} élément(s) dépublié(s).", messages.SUCCESS)


class ServiceManagedAdminMixin:
    """
    Fiche pilotée par les services (réservation, devis, message, avis) : le
    statut n'est jamais un champ du formulaire, et l'enregistrement ne réécrit
    que les champs modifiés. Un statut changé entre-temps (le client annule ou
    accepte pendant que la fiche est ouverte) n'est donc jamais écrasé.
    Les boutons unfold de la ligne d'enregistrement (actions_submit_line)
    s'exécutent ensuite, comme dans unfold.
    """

    def save_changed_fields(self, obj, form):
        concrete = {field.name for field in obj._meta.concrete_fields}
        fields = [name for name in form.changed_data if name in concrete]
        if fields:
            obj.save(update_fields=[*fields, "updated_at"])

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return
        self.save_changed_fields(obj, form)
        for submit_action in self.get_actions_submit_line(request, obj.pk):
            if submit_action.action_name in request.POST:
                submit_action.method(request, obj)


class SoftDeleteAdminMixin:
    """
    Suppression logique (SoftDeleteModel) : l'objet disparaît des listes mais
    reste en base. QuerySet.delete() supprimerait réellement : on passe par
    Model.delete() pour chaque objet.
    """

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()


# --- Décisions métier depuis l'admin -----------------------------------------


class DecisionForm(forms.Form):
    """Formulaire vide : simple confirmation d'une décision."""


class ReasonForm(forms.Form):
    reason = forms.CharField(
        label="Motif",
        required=False,
        max_length=1000,
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 4}),
    )


def date_input():
    return forms.DateInput(attrs={"type": "date", "class": " ".join(INPUT_CLASSES)},
                           format="%Y-%m-%d")


def run_for_each(model_admin, request, queryset, service, done_label):
    """Action groupée : applique un service à chaque objet, erreurs métier comprises."""
    done, errors = 0, []
    for obj in queryset:
        try:
            service(obj)
        except BusinessError as exc:
            errors.append(f"{obj} : {exc.message}")
        else:
            done += 1
    if done:
        model_admin.message_user(request, f"{done} {done_label}.", messages.SUCCESS)
    for error in errors:
        model_admin.message_user(request, error, messages.ERROR)


def decision_view(
    model_admin, request, object_id, *, title, submit_label, perform,
    form_class=DecisionForm, description="", initial=None, summary=(),
):
    """
    Page de décision (action de détail unfold) : GET affiche le formulaire de
    confirmation, POST appelle le service. perform(obj, cleaned_data) renvoie
    le message de succès ; une BusinessError reste affichée sur la page.
    """
    obj = model_admin.get_object(request, object_id)
    opts = model_admin.model._meta
    if obj is None:
        return model_admin._get_obj_does_not_exist_redirect(request, opts, object_id)
    change_url = reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk])

    form = form_class(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            success = perform(obj, form.cleaned_data)
        except BusinessError as exc:
            form.add_error(None, exc.message)
        else:
            model_admin.message_user(request, success, messages.SUCCESS)
            return redirect(change_url)

    context = {
        **model_admin.admin_site.each_context(request),
        "opts": opts,
        "original": obj,
        "title": title,
        "description": description,
        "summary": summary,
        "form": form,
        "submit_label": submit_label,
        "change_url": change_url,
    }
    return TemplateResponse(request, "admin/decision_form.html", context)


def list_decision_view(model_admin, request, *, title, submit_label, perform, description=""):
    """
    Action de liste unfold (un lien) qui modifie des données : GET affiche une
    confirmation, POST appelle perform() → (niveau, message), puis retour à la liste.
    """
    opts = model_admin.model._meta
    changelist = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
    if request.method != "POST":
        context = {
            **model_admin.admin_site.each_context(request),
            "opts": opts,
            "title": title,
            "description": description,
            "form": DecisionForm(),
            "submit_label": submit_label,
            "change_url": changelist,
        }
        return TemplateResponse(request, "admin/decision_form.html", context)
    level, message = perform()
    model_admin.message_user(request, message, level)
    return redirect(changelist)


# --- Réglages transverses -----------------------------------------------------


@admin.register(Category)
class CategoryAdmin(TranslatedAdmin):
    list_display = ("name", "kind", "slug", "order")
    list_filter = ("kind",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("kind", "order", "name")


@admin.register(Tag)
class TagAdmin(TranslatedAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslatedAdmin):
    """Paramètres du site : une seule fiche (pk=1), ouverte directement."""

    fieldsets = (
        ("Agence", {"fields": ("agency_name", "slogan", "phone", "email", "whatsapp",
                               "address", "opening_hours", "latitude", "longitude")}),
        ("Accueil", {"fields": ("hero_subtitle", "hero_image", "hero_video_url")}),
        ("Réseaux sociaux", {"fields": ("social_links",)}),
        ("Page « À propos »", {"fields": ("about_content",)}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse("admin:core_sitesettings_change", args=[obj.pk]))


@admin.register(ExchangeRate)
class ExchangeRateAdmin(BaseAdmin):
    list_display = ("currency", "rate_from_xof", "one_unit_in_xof", "fetched_at")
    actions_list = ("refresh_rates",)

    @display(description="1 unité en FCFA")
    def one_unit_in_xof(self, obj):
        return format_amount(1 / obj.rate_from_xof, "XOF") if obj.rate_from_xof else "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        transaction.on_commit(lambda: cache.delete(RATES_CACHE_KEY))

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        transaction.on_commit(lambda: cache.delete(RATES_CACHE_KEY))

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        transaction.on_commit(lambda: cache.delete(RATES_CACHE_KEY))

    @action(description="Mettre à jour les taux maintenant", url_path="refresh",
            permissions=["change"], icon="sync")
    def refresh_rates(self, request):
        def perform():
            try:
                update_exchange_rates()
            except Exception:  # noqa: BLE001 — service externe : on informe sans planter l'admin
                return messages.ERROR, "Service des taux indisponible, réessayez plus tard."
            return messages.SUCCESS, "Taux de change mis à jour."

        return list_decision_view(
            self, request,
            title="Mettre à jour les taux de change",
            description="Les taux EUR → USD et GBP sont récupérés auprès de la BCE ; "
                        "l'euro reste à parité fixe (1 EUR = 655,957 FCFA).",
            submit_label="Mettre à jour",
            perform=perform,
        )
