"""
Point d'entrée unique de l'API v1 (architecture § 5.2).
Le tableau de bord (Phase 19) est dans l'admin Django.
"""
from django.urls import include, path

from apps.core.views import CurrencyView, SitemapView, SiteSettingsView, health

APPS_WITH_ROUTES = [
    "accounts", "core", "destinations", "tours", "accommodations", "vehicles", "activities", "events",
    "media", "offers", "blog", "services", "visas", "transport", "inquiries", "bookings",
    "reviews", "notifications", "search",
]

urlpatterns = [
    path("health/", health, name="health-check"),
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("currencies/", CurrencyView.as_view(), name="currencies"),
    path("seo/sitemap/", SitemapView.as_view(), name="sitemap"),
] + [path("", include(f"apps.{app}.urls")) for app in APPS_WITH_ROUTES]
