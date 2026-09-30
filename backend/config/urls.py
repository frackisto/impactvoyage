from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.authentication import SessionAuthentication

from apps.accounts import two_factor_views
from apps.accounts.permissions import ApiDocsPermission

# Documentation de l'API : réservée en production à l'équipe connectée au backoffice
# (session vérifiée par la double authentification), voir API_DOCS_PUBLIC.
docs = {"permission_classes": [ApiDocsPermission],
        "authentication_classes": [SessionAuthentication]}

urlpatterns = [
    # Adresse non standard en production (ADMIN_URL_PATH) ; double authentification
    # de l'équipe (apps/accounts/middleware.py) avant l'accès au backoffice.
    path(f"{settings.ADMIN_URL}2fa/", two_factor_views.verify, name="admin-2fa-verify"),
    path(f"{settings.ADMIN_URL}2fa/setup/", two_factor_views.setup, name="admin-2fa-setup"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include("config.api_urls")),
    # Documentation OpenAPI / Swagger
    path("api/v1/schema/", SpectacularAPIView.as_view(**docs), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema", **docs),
        name="swagger-ui",
    ),
    path(
        "api/v1/redoc/",
        SpectacularRedocView.as_view(url_name="schema", **docs),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
