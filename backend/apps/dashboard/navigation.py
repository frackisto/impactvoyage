"""
Menu latéral du backoffice (UNFOLD["SIDEBAR"]) : chaque entrée n'apparaît que
si le rôle peut consulter la ressource (accounts.roles), et une rubrique vide
disparaît. Les pastilles comptent le travail en attente.
"""
from django.urls import reverse_lazy

from apps.bookings.models import Booking
from apps.inquiries.models import ContactMessage, QuoteRequest
from apps.notifications.models import Notification
from apps.reviews.models import Review

from .selectors import BOOKINGS_TO_PROCESS

TEAM = "team"  # tout membre de l'équipe (ses propres notifications)


def _entry(title, icon, model, badge=None):
    app_label, model_name = model.split(".")
    entry = {
        "title": title,
        "icon": icon,
        "link": reverse_lazy(f"admin:{app_label}_{model_name}_changelist"),
        "perm": f"{app_label}.view_{model_name}",
    }
    if badge:
        entry["badge"] = f"apps.dashboard.navigation.{badge}"
        entry["badge_variant"] = "primary"
    return entry


SECTIONS = (
    (None, (
        {"title": "Tableau de bord", "icon": "dashboard", "link": reverse_lazy("admin:index"),
         "perm": TEAM},
        {**_entry("Mes notifications", "notifications", "notifications.notification",
                  badge="unread_notifications"), "perm": TEAM},
    )),
    ("Relation client", (
        _entry("Devis", "request_quote", "inquiries.quoterequest", badge="open_quotes"),
        _entry("Réservations", "event_available", "bookings.booking", badge="bookings_to_process"),
        _entry("Messages", "mail", "inquiries.contactmessage", badge="unread_messages"),
        _entry("Avis clients", "reviews", "reviews.review", badge="pending_reviews"),
    )),
    ("Catalogue", (
        _entry("Destinations", "public", "destinations.destination"),
        _entry("Circuits", "route", "tours.tour"),
        _entry("Hôtels", "hotel", "accommodations.hotel"),
        _entry("Résidences", "apartment", "accommodations.residence"),
        _entry("Véhicules", "directions_car", "vehicles.vehicle"),
        _entry("Activités", "hiking", "activities.activity"),
        _entry("Événements", "celebration", "events.event"),
        _entry("Offres", "local_offer", "offers.offer"),
    )),
    ("Contenus", (
        _entry("Services", "room_service", "services.service"),
        _entry("Visas", "contract", "visas.visaservice"),
        _entry("Transport", "airport_shuttle", "transport.transportservice"),
        _entry("Blog", "article", "blog.blogpost"),
        _entry("Médiathèque", "photo_library", "media.mediaalbum"),
        _entry("Catégories", "category", "core.category"),
        _entry("Tags", "sell", "core.tag"),
        _entry("Équipements", "pool", "accommodations.amenity"),
    )),
    ("Administration", (
        _entry("Utilisateurs", "group", "accounts.user"),
        _entry("Paramètres du site", "settings", "core.sitesettings"),
        _entry("Taux de change", "currency_exchange", "core.exchangerate"),
        _entry("Paiements", "payments", "payments.payment"),
    )),
)


def _allowed(user, perm):
    if perm == TEAM:
        return user.is_active and user.is_staff
    return user.has_perm(perm)


def sidebar_navigation(request):
    navigation = []
    for title, entries in SECTIONS:
        items = [
            {key: value for key, value in entry.items() if key != "perm"}
            for entry in entries
            if _allowed(request.user, entry["perm"])
        ]
        if items:
            navigation.append({"title": title, "separator": title is not None, "items": items})
    return navigation


# --- Pastilles (None : rien à signaler, la pastille est masquée) ---------------


def _count(queryset):
    return queryset.count() or None


def unread_notifications(request):
    return _count(Notification.objects.filter(recipient=request.user, is_read=False))


def open_quotes(request):
    return _count(QuoteRequest.objects.filter(status=QuoteRequest.Status.NOUVELLE))


def bookings_to_process(request):
    return _count(Booking.objects.filter(status__in=BOOKINGS_TO_PROCESS))


def unread_messages(request):
    return _count(ContactMessage.objects.filter(status=ContactMessage.Status.NOUVEAU))


def pending_reviews(request):
    return _count(Review.objects.filter(status=Review.Status.EN_ATTENTE))
