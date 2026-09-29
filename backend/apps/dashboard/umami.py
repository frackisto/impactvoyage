"""
Nombre de visiteurs, lu dans Umami (auto-hébergé, sans cookie ; architecture § 13).
Django ne journalise pas les visites lui-même. Umami est déployé en Phase 24 :
tant que UMAMI_API_URL, UMAMI_WEBSITE_ID et UMAMI_API_TOKEN sont vides, le
tableau de bord indique que la mesure n'est pas branchée.
"""
import json
import logging
from datetime import timedelta
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

CACHE_KEY = "dashboard:umami"
FAILURE_CACHE_SECONDS = 60
DAYS = 30


def is_configured():
    return bool(settings.UMAMI_API_URL and settings.UMAMI_WEBSITE_ID and settings.UMAMI_API_TOKEN)


def _metric(payload, name):
    """Umami 2.x renvoie {"visitors": {"value": n}}, les versions récentes {"visitors": n}."""
    value = payload[name]
    if isinstance(value, dict):
        value = value["value"]
    return int(value)


def fetch_stats(days=DAYS, now=None):
    now = now or timezone.now()
    start = now - timedelta(days=days)
    url = (
        f"{settings.UMAMI_API_URL.rstrip('/')}/api/websites/{settings.UMAMI_WEBSITE_ID}/stats"
        f"?startAt={int(start.timestamp() * 1000)}&endAt={int(now.timestamp() * 1000)}"
    )
    request = Request(url, headers={
        "Authorization": f"Bearer {settings.UMAMI_API_TOKEN}",
        "Accept": "application/json",
        "User-Agent": "impactvoyage/1.0",
    })
    with urlopen(request, timeout=3) as response:  # noqa: S310 (URL fixée par la config)
        payload = json.load(response)
    return {"visitors": _metric(payload, "visitors"), "pageviews": _metric(payload, "pageviews"),
            "days": days}


def visitor_stats():
    """
    {"visitors", "pageviews", "days"} sur 30 jours ; {"unavailable": True} si Umami
    ne répond pas ; None si la mesure n'est pas configurée.
    """
    if not is_configured():
        return None
    stats = cache.get(CACHE_KEY)
    if stats is None:
        try:
            stats = fetch_stats()
        except (URLError, OSError, ValueError, KeyError, TypeError):
            logger.warning("Statistiques Umami indisponibles.", exc_info=True)
            stats = {"unavailable": True}
            cache.set(CACHE_KEY, stats, FAILURE_CACHE_SECONDS)
        else:
            cache.set(CACHE_KEY, stats, settings.DASHBOARD_CACHE_SECONDS)
    return stats
