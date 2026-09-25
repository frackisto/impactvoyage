"""
Point d'entrée unique de l'API v1 (architecture § 5.2).
La recherche globale (/search/) arrive en Phase 16, le tableau de bord en Phase 19.
"""
from django.urls import include, path

from apps.core.views import CurrencyView, SiteSettingsView, health

APPS_WITH_ROUTES = [
    "accounts", "core", "destinations", "tours", "accommodations", "vehicles", "activities", "events",
    "media", "offers", "blog", "services", "visas", "transport", "inquiries", "bookings",
    "reviews", "notifications",
]

urlpatterns = [
    path("health/", health, name="health-check"),
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("currencies/", CurrencyView.as_view(), name="currencies"),
] + [path("", include(f"apps.{app}.urls")) for app in APPS_WITH_ROUTES]
