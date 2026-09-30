from django.conf import settings
from rest_framework.permissions import BasePermission

from .otp import otp_required


def is_verified_staff(user):
    """Membre de l'équipe dont la session a passé la double authentification (si exigée)."""
    if not (user and user.is_authenticated and user.is_staff):
        return False
    return not otp_required(user) or getattr(user, "is_verified", lambda: False)()


class ApiDocsPermission(BasePermission):
    """Documentation de l'API : publique si API_DOCS_PUBLIC, sinon équipe connectée à l'admin."""

    def has_permission(self, request, view):
        return settings.API_DOCS_PUBLIC or is_verified_staff(request.user)
