"""
Comptes dans le backoffice. Le rôle est la seule source de vérité (accounts.roles) :
is_staff, is_superuser et le groupe en sont dérivés, ils ne sont donc pas
éditables ici et les groupes Django disparaissent de l'admin.

Garde-fou contre l'élévation de privilèges : seul un super administrateur peut
attribuer ce rôle ou modifier le compte d'un super administrateur.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.core.admin import BaseAdmin

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


class AccountCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "role")


class AccountChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(DjangoUserAdmin, BaseAdmin):
    form = AccountChangeForm
    add_form = AccountCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("email", "full_name", "role_label", "is_active", "is_verified", "last_login")
    list_filter = ("role", "is_active", "is_verified")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("email",)
    filter_horizontal = ()
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("first_name", "last_name", "phone", "whatsapp",
                                 "country_code", "avatar")}),
        ("Rôle et accès", {"fields": ("role", "is_active", "is_verified")}),
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
