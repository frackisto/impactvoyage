"""
Comptes dans le backoffice. Le rôle est la seule source de vérité (accounts.roles) :
is_staff, is_superuser et le groupe en sont dérivés, ils ne sont donc pas
éditables ici et les groupes Django disparaissent de l'admin.

Garde-fou contre l'élévation de privilèges : seul un super administrateur peut
attribuer ce rôle ou modifier le compte d'un super administrateur.

Double authentification (Phase 23) : les appareils django-otp ne sont pas gérés
ici ; un super administrateur peut seulement réinitialiser celle d'un membre de
l'équipe (téléphone perdu), qui en enregistre une nouvelle à sa connexion suivante.

Données personnelles (Phase 23) : bouton « Données personnelles » de la liste,
réservé aux administrateurs : export (droit d'accès) et effacement d'après une
adresse email, compte ou non (apps/core/privacy.py).
"""
import json

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.widgets import UnfoldAdminEmailInputWidget, UnfoldBooleanWidget

from apps.core import privacy
from apps.core.admin import BaseAdmin, decision_view

from . import otp
from .models import User

ROLE_LABELS = {
    User.Role.SUPER_ADMIN: "danger",
    User.Role.ADMIN: "warning",
    User.Role.AGENT: "primary",
    User.Role.COMMERCIAL: "primary",
    User.Role.GESTIONNAIRE: "primary",
    User.Role.CLIENT: "default",
}

admin.site.unregister(Group)
for _model in (TOTPDevice, StaticDevice):
    if admin.site.is_registered(_model):
        admin.site.unregister(_model)


class AccountCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "role")


class AccountChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


class PersonalDataForm(forms.Form):
    email = forms.EmailField(label="Adresse email de la personne",
                             widget=UnfoldAdminEmailInputWidget())
    confirm = forms.BooleanField(
        label="J'ai vérifié l'identité du demandeur et je confirme l'effacement.",
        required=False, widget=UnfoldBooleanWidget(),
    )


@admin.register(User)
class UserAdmin(DjangoUserAdmin, BaseAdmin):
    form = AccountChangeForm
    add_form = AccountCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("email", "full_name", "role_label", "is_active", "is_verified", "two_factor",
                    "last_login")
    list_filter = ("role", "is_active", "is_verified")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("email",)
    filter_horizontal = ()
    readonly_fields = ("last_login", "date_joined", "two_factor")
    actions_detail = ("reset_two_factor",)
    actions_list = ("personal_data",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("first_name", "last_name", "phone", "whatsapp",
                                 "country_code", "avatar")}),
        ("Rôle et accès", {"fields": ("role", "is_active", "is_verified", "two_factor")}),
        ("Préférences", {"fields": ("preferred_language", "preferred_currency")}),
        ("Historique", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "role", "password1", "password2")}),
    )

    @display(description="nom", ordering="last_name")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @display(description="rôle", ordering="role", label=ROLE_LABELS)
    def role_label(self, obj):
        return obj.role, obj.get_role_display()

    def get_queryset(self, request):
        # Colonne « double authentification » sans une requête par ligne.
        confirmed = TOTPDevice.objects.filter(user=OuterRef("pk"), confirmed=True)
        return super().get_queryset(request).annotate(has_totp=Exists(confirmed))

    @display(description="double authentification", label={True: "success", False: "warning"})
    def two_factor(self, obj):
        if obj is None or not obj.is_staff:
            return "—"
        enabled = obj.has_totp
        return enabled, "Activée" if enabled else "À configurer"

    @action(description="Réinitialiser la double authentification", url_path="reset-2fa",
            permissions=["reset_two_factor"], icon="phonelink_erase")
    def reset_two_factor(self, request, object_id):
        def perform(user, data):
            otp.reset_devices(user)
            return (f"Double authentification réinitialisée : {user.email} enregistrera "
                    "une nouvelle application à sa prochaine connexion.")

        return decision_view(
            self, request, object_id, title="Réinitialiser la double authentification",
            submit_label="Réinitialiser", perform=perform,
            description="À utiliser si ce membre de l'équipe a perdu son téléphone et ses "
                        "codes de secours. Vérifiez son identité avant de confirmer.",
        )

    def has_reset_two_factor_permission(self, request, object_id=None):
        return request.user.is_superuser

    @action(description="Données personnelles", url_path="personal-data",
            permissions=["personal_data"], icon="shield_person")
    def personal_data(self, request):
        """
        Droit d'accès et d'effacement pour une adresse email. Tout passe en POST :
        l'adresse ne figure jamais dans une URL (journaux du serveur).
        """
        form = PersonalDataForm(request.POST or None)
        context = {**self.admin_site.each_context(request), "opts": self.model._meta,
                   "title": "Données personnelles", "form": form}
        if form.is_valid():
            email = form.cleaned_data["email"]
            step = request.POST.get("step")
            if step == "export":
                return self._export_response(email)
            if step == "erase":
                if form.cleaned_data["confirm"]:
                    context["summary"] = [
                        (label, [(privacy.DECISION_LABELS[key], n) for key, n in counts.items() if n])
                        for label, counts in privacy.erase_personal_data(email)
                    ]
                    self.message_user(request, "Données personnelles effacées ; les "
                                      "enregistrements conservés sont indiqués ci-dessous.",
                                      messages.SUCCESS)
                else:
                    form.add_error("confirm", "Cochez la case pour confirmer l'effacement.")
            context["email"] = email
            context["found"] = privacy.find_personal_data(email)
        return TemplateResponse(request, "admin/personal_data.html", context)

    @staticmethod
    def _export_response(email):
        data = privacy.export_personal_data(email)
        response = HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8",
        )
        filename = f"donnees-personnelles-{timezone.localdate():%Y%m%d}.json"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def has_personal_data_permission(self, request):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "role" and not request.user.is_superuser:
            kwargs["choices"] = [c for c in User.Role.choices if c[0] != User.Role.SUPER_ADMIN]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def _protects_superuser(self, request, obj):
        return obj is not None and obj.is_superuser and not request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if self._protects_superuser(request, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._protects_superuser(request, obj):
            return False
        return super().has_delete_permission(request, obj)
