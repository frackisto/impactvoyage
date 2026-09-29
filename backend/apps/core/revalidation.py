"""
Régénération à la demande des pages du site (Phase 21, architecture § 9).

Quand un contenu public change (admin, services, commandes), le site Next.js
doit l'afficher sans attendre l'expiration de son cache (5 minutes). Chaque
modèle public correspond à des étiquettes de cache du frontend (fetch `tags`) ;
après validation de la transaction, une tâche Celery appelle
POST {FRONTEND_REVALIDATE_URL} {"tags": [...]} avec le secret partagé.

Les étiquettes d'une même transaction sont regroupées en un seul appel.
Les modifications groupées (QuerySet.update, qui n'émet pas de signal) appellent
revalidate_model() explicitement. Désactivé si FRONTEND_REVALIDATE_URL est vide.
"""
import json
import logging
import threading
from urllib.error import URLError
from urllib.request import Request, urlopen

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save

logger = logging.getLogger(__name__)

SITEMAP = "sitemap"
BOOKABLE = ("tours", "hotels", "residences", "vehicles", "activities")

# Modèle → étiquettes de cache du frontend (frontend/services/*.service.ts).
MODEL_TAGS = {
    "destinations.destination": ("destinations", "tours", "hotels", "residences", "activities",
                                 SITEMAP),
    "destinations.destinationimage": ("destinations",),
    "tours.tour": ("tours", "offers", SITEMAP),
    "tours.tourimage": ("tours",),
    "tours.tourday": ("tours",),
    "tours.tourdeparture": ("tours",),  # places restantes
    "accommodations.hotel": ("hotels", "offers", SITEMAP),
    "accommodations.hotelimage": ("hotels",),
    "accommodations.room": ("hotels",),
    "accommodations.amenity": ("hotels", "residences"),
    "accommodations.residence": ("residences", "offers", SITEMAP),
    "accommodations.residenceimage": ("residences",),
    "vehicles.vehicle": ("vehicles", "offers", SITEMAP),
    "vehicles.vehicleimage": ("vehicles",),
    "activities.activity": ("activities", "tours", "offers", SITEMAP),
    "activities.activityimage": ("activities",),
    "events.event": ("events", SITEMAP),
    "events.eventimage": ("events",),
    "media.mediaalbum": ("media", SITEMAP),
    "media.mediaitem": ("media",),
    "offers.offer": ("offers", *BOOKABLE, SITEMAP),  # prix promotionnels sur les fiches
    "services.service": ("services",),
    "services.serviceprice": ("services",),
    "visas.visaservice": ("visas", SITEMAP),
    "transport.transportservice": ("transport",),
    "blog.blogpost": ("blog", SITEMAP),
    "core.category": ("categories", "tours", "activities", "blog", "media"),
    "core.tag": ("blog", "destinations"),
    "core.sitesettings": ("site-settings",),
    "reviews.review": ("reviews", "tours", "hotels", "destinations", "activities"),
}

_pending = threading.local()


def tags_for(model):
    return MODEL_TAGS.get(model._meta.label_lower, ())


def request_revalidation(tags):
    """Programme la régénération des étiquettes après validation de la transaction."""
    if not settings.FRONTEND_REVALIDATE_URL or not tags:
        return
    pending = getattr(_pending, "tags", None)
    if pending is None:
        pending = _pending.tags = set()
    pending.update(tags)
    # Le premier _flush exécuté après la validation envoie toutes les étiquettes ; les
    # suivants trouvent l'ensemble vide et ne font rien. Une transaction annulée perd ses
    # appels, et ses étiquettes partent avec la prochaine modification validée.
    transaction.on_commit(_flush)


def revalidate_model(model):
    """Pour les modifications groupées (QuerySet.update) qui n'émettent aucun signal."""
    request_revalidation(tags_for(model))


def _flush():
    tags = sorted(getattr(_pending, "tags", None) or ())
    _pending.tags = None
    if tags:
        revalidate_frontend_task.delay(tags)


@shared_task(autoretry_for=(URLError, OSError), retry_backoff=10, max_retries=3)
def revalidate_frontend_task(tags):
    """Appelle la route /api/revalidate du site (secret partagé FRONTEND_SHARED_SECRET)."""
    request = Request(
        settings.FRONTEND_REVALIDATE_URL,
        data=json.dumps({"tags": tags}).encode(),
        method="POST",
        headers={"Content-Type": "application/json",
                 "X-Frontend-Secret": settings.FRONTEND_SHARED_SECRET},
    )
    with urlopen(request, timeout=10) as response:  # noqa: S310 (URL fixée par la config)
        logger.info("Pages régénérées (%s) : %s", response.status, ", ".join(tags))


def _on_change(sender, instance=None, raw=False, **kwargs):
    if not raw:  # chargement de fixtures : rien à régénérer
        request_revalidation(tags_for(sender))


def _on_m2m_change(sender, instance=None, action="", **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        request_revalidation(tags_for(type(instance)))


def connect_signals():
    for label in MODEL_TAGS:
        model = apps.get_model(label)
        uid = f"revalidate-{label}"
        post_save.connect(_on_change, sender=model, dispatch_uid=f"{uid}-save")
        post_delete.connect(_on_change, sender=model, dispatch_uid=f"{uid}-delete")
        for field in model._meta.many_to_many:
            m2m_changed.connect(_on_m2m_change, sender=field.remote_field.through,
                                dispatch_uid=f"{uid}-{field.name}")
