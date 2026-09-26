"""
Socle de l'API REST (architecture § 5.1) : format d'erreur unique,
permissions de base, limitation de débit des formulaires et ViewSets de lecture
branchés sur les selectors.
"""
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, permissions, viewsets
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler

from .exceptions import BusinessError
from .throttling import ScopedRateThrottle


def error_body(code, message, details=None):
    return {"error": {"code": code, "message": message, "details": details or {}}}


def api_exception_handler(exc, context):
    """
    Toutes les erreurs de l'API ont la même forme :
    {"error": {"code": "validation_error", "message": "…", "details": {…}}}
    """
    if isinstance(exc, BusinessError):
        return Response(error_body(exc.code, exc.message, exc.details), status=exc.status_code)
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))
    elif isinstance(exc, (Http404, ObjectDoesNotExist)):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None:  # erreur inattendue : Django renvoie une 500 (et la journalise)
        return None

    if isinstance(exc, exceptions.ValidationError):
        response.data = error_body("validation_error", "Données invalides.", response.data)
    else:
        detail = response.data.get("detail", "") if isinstance(response.data, dict) else ""
        details = {"wait": exc.wait} if isinstance(exc, exceptions.Throttled) else {}
        response.data = error_body(getattr(detail, "code", exc.default_code), str(detail), details)
    return response


def has_perm(*perms):
    """
    Permission DRF exigeant des permissions Django (dérivées du rôle, voir
    accounts.roles), ex. has_perm("bookings.change_booking").
    """

    class HasPerm(permissions.BasePermission):
        message = "Votre rôle ne permet pas cette action."

        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.has_perms(perms))

    HasPerm.__name__ = f"HasPerm({', '.join(perms)})"
    return HasPerm


class IsStaff(permissions.BasePermission):
    """Membre de l'équipe (tout rôle sauf CLIENT) ; les droits fins passent par has_perm."""

    message = "Réservé à l'équipe de l'agence."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class WriteThrottleMixin:
    """
    Applique le scope de débit (settings REST_FRAMEWORK) aux seules actions
    d'écriture publiques : consulter la liste des avis ne consomme pas le quota
    d'envoi d'avis.
    """

    write_throttle_scope = None
    throttled_actions = ("create",)

    def get_throttles(self):
        throttles = super().get_throttles()
        if self.write_throttle_scope and getattr(self, "action", None) in self.throttled_actions:
            self.throttle_scope = self.write_throttle_scope
            throttles.append(ScopedRateThrottle())
        return throttles


class SelectorReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lecture publique branchée sur les selectors :
    - list : list_selector(**paramètres validés par filter_params_class) ;
    - retrieve : detail_selector(slug), 404 si absent ou non publié.
    La recherche (?search=) et le tri (?ordering=) passent par les backends DRF.
    """

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    list_selector = None
    detail_selector = None
    filter_params_class = None
    detail_serializer_class = None

    def get_filter_params(self):
        if self.filter_params_class is None:
            return {}
        params = self.filter_params_class(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        return {k: v for k, v in params.validated_data.items() if v not in (None, "", [])}

    def get_queryset(self):
        return type(self).list_selector(**self.get_filter_params())

    def get_object(self):
        try:
            obj = type(self).detail_selector(self.kwargs[self.lookup_field])
        except ObjectDoesNotExist as exc:
            raise exceptions.NotFound() from exc
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_class(self):
        if self.action == "retrieve" and self.detail_serializer_class:
            return self.detail_serializer_class
        return super().get_serializer_class()
