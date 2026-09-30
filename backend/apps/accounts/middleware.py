"""
Protection du backoffice (Phase 23, architecture § 11).

- AdminLoginThrottleMiddleware : après ADMIN_LOGIN_MAX_FAILURES échecs de connexion
  pour une même adresse IP ou un même compte, les essais sont refusés pendant
  ADMIN_LOGIN_LOCKOUT_SECONDS (force brute).
- AdminTwoFactorMiddleware : un membre de l'équipe connecté par mot de passe doit
  encore saisir un code de son application (ou l'enregistrer) avant d'accéder au
  backoffice. Placé après OTPMiddleware (request.user.is_verified()).
"""
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework.throttling import BaseThrottle

from .otp import has_confirmed_device, otp_required


def client_ip(request):
    """Adresse du visiteur ; X-Forwarded-For n'est lu que derrière un proxy déclaré (NUM_PROXIES)."""
    return BaseThrottle().get_ident(request)


class AdminLoginThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method != "POST" or request.path != reverse("admin:login"):
            return self.get_response(request)

        keys = [f"admin-login:ip:{client_ip(request)}"]
        username = request.POST.get("username", "").strip().lower()
        if username:
            keys.append(f"admin-login:user:{username}")
        if any(cache.get(key, 0) >= settings.ADMIN_LOGIN_MAX_FAILURES for key in keys):
            return render(request, "admin/login_locked.html", {
                **admin.site.each_context(request),
                "title": "Connexion",
                "minutes": settings.ADMIN_LOGIN_LOCKOUT_SECONDS // 60,
            }, status=429)

        response = self.get_response(request)
        if response.status_code == 200:  # formulaire réaffiché : identifiants refusés
            for key in keys:
                cache.add(key, 0, settings.ADMIN_LOGIN_LOCKOUT_SECONDS)
                cache.incr(key)
        elif response.status_code == 302:  # connexion réussie
            cache.delete_many(keys)
        return response


class AdminTwoFactorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.prefix = "/" + settings.ADMIN_URL

    def __call__(self, request):
        if request.path.startswith(self.prefix) and self._must_verify(request):
            exempt = {reverse(name) for name in (
                "admin:login", "admin:logout", "admin:jsi18n",
                "admin-2fa-verify", "admin-2fa-setup",
            )}
            if request.path not in exempt:
                target = "admin-2fa-verify" if has_confirmed_device(request.user) else "admin-2fa-setup"
                url = reverse(target)
                if request.method == "GET":
                    url += "?" + urlencode({"next": request.get_full_path()})
                return redirect(url)
        return self.get_response(request)

    @staticmethod
    def _must_verify(request):
        user = request.user
        return otp_required(user) and not user.is_verified()
