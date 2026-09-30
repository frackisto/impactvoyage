"""
Pages de double authentification du backoffice (voir apps/accounts/otp.py).

- /<admin>/2fa/setup/ : premier accès, enregistrement de l'application (QR code),
  confirmé par un premier code ; les codes de secours s'affichent une seule fois.
- /<admin>/2fa/ : saisie d'un code à chaque connexion.

Un compte qui a déjà une application ne peut pas en enregistrer une autre sans
code : le mot de passe seul ne suffit jamais à prendre la main sur le compte.
"""
import segno
from django import forms
from django.contrib import admin
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django_otp import login as otp_login
from unfold.widgets import UnfoldAdminTextInputWidget

from . import otp


class CodeForm(forms.Form):
    code = forms.CharField(
        label="Code", max_length=16,
        widget=UnfoldAdminTextInputWidget(attrs={
            "autocomplete": "one-time-code", "inputmode": "text", "autofocus": True,
            "autocapitalize": "off", "spellcheck": "false",
        }),
    )


def _next_url(request):
    url = request.POST.get("next") or request.GET.get("next") or ""
    if url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()},
                                       require_https=request.is_secure()):
        return url
    return reverse("admin:index")


def _render(request, template, **context):
    return TemplateResponse(request, template, {
        **admin.site.each_context(request),
        "next": _next_url(request),
        **context,
    })


def _staff_only(view):
    def wrapper(request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect_to_login(request.get_full_path(), reverse("admin:login"))
        if not otp.otp_required(request.user) or request.user.is_verified():
            return redirect(_next_url(request))
        return view(request)
    wrapper.__name__ = view.__name__
    return never_cache(sensitive_post_parameters("code")(wrapper))


def _login(request, device):
    """Session vérifiée : nouvelle clé de session (élévation de privilège)."""
    request.session.cycle_key()
    otp_login(request, device)


@_staff_only
def verify(request):
    user = request.user
    if not otp.has_confirmed_device(user):
        return redirect("admin-2fa-setup")
    form = CodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        device = otp.verify_code(user, form.cleaned_data["code"])
        if device is not None:
            _login(request, device)
            return redirect(_next_url(request))
        form.add_error("code", "Code incorrect ou expiré. Attendez quelques secondes "
                               "avant un nouvel essai.")
    return _render(request, "admin/two_factor/verify.html",
                   title="Double authentification", form=form)


@_staff_only
def setup(request):
    user = request.user
    if otp.has_confirmed_device(user):
        return redirect("admin-2fa-verify")
    device = otp.pending_totp_device(user)
    form = CodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        codes = otp.confirm_totp_device(device, form.cleaned_data["code"])
        if codes is not None:
            device.refresh_from_db()
            _login(request, device)
            return _render(request, "admin/two_factor/backup_codes.html",
                           title="Codes de secours", codes=codes)
        form.add_error("code", "Code incorrect. Vérifiez l'heure de votre téléphone et "
                               "saisissez le code affiché.")
    qr = segno.make(device.config_url, error="m")
    return _render(
        request, "admin/two_factor/setup.html",
        title="Activer la double authentification", form=form,
        # SVG produit par segno à partir de l'URI otpauth : aucun contenu saisi.
        qr_svg=mark_safe(qr.svg_inline(scale=5, dark="#0b1f33", light="#ffffff")),  # noqa: S308
        secret=_group(device.config_url),
    )


def _group(config_url):
    """Clé secrète (base32) en groupes de 4 caractères, pour une saisie manuelle."""
    secret = config_url.split("secret=", 1)[1].split("&", 1)[0]
    return " ".join(secret[i:i + 4] for i in range(0, len(secret), 4))
