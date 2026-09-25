"""
Matrice rôles → permissions (architecture § 6.2, § 6.3 ; CdC § 23).

Seule source de vérité des droits : la commande `sync_roles` (lancée aussi
après chaque migrate) en dérive un groupe Django par rôle, et chaque
utilisateur est placé dans le groupe de son rôle. Les mêmes permissions Django
servent à l'API (apps.core.api.has_perm) et à l'admin (Phase 19).

Les permissions sont exprimées par ressource métier avec les actions du cahier
des charges (view, create, update, delete), traduites en permissions Django
(view_, add_, change_, delete_ sur chaque modèle de la ressource).
"""
from .models import User

VIEW = ("view",)
MANAGE = ("view", "create", "update")
ALL = ("view", "create", "update", "delete")

# Ressource métier → modèles concernés ("app_label.model").
RESOURCES = {
    "destinations": ["destinations.destination", "destinations.destinationimage"],
    "tours": ["tours.tour", "tours.tourimage", "tours.tourday", "tours.tourdeparture"],
    "accommodations": [
        "accommodations.hotel", "accommodations.hotelimage", "accommodations.room",
        "accommodations.amenity",
    ],
    "residences": ["accommodations.residence", "accommodations.residenceimage"],
    "vehicles": ["vehicles.vehicle", "vehicles.vehicleimage"],
    "activities": ["activities.activity", "activities.activityimage"],
    "events": ["events.event", "events.eventimage"],
    "media": ["media.mediaalbum", "media.mediaitem"],
    "offers": ["offers.offer"],
    "services": ["services.service"],
    "visas": ["visas.visaservice"],
    "transport": ["transport.transportservice"],
    "blog": ["blog.blogpost"],
    "taxonomy": ["core.category", "core.tag"],
    "quotes": ["inquiries.quoterequest"],
    "contacts": ["inquiries.contactmessage"],
    "bookings": ["bookings.booking", "bookings.bookingitem"],
    "reviews": ["reviews.review"],
    "payments": ["payments.payment", "payments.paymenttransaction"],
    "site_settings": ["core.sitesettings", "core.exchangerate"],
    "users": ["accounts.user"],
}

CATALOG = (
    "destinations", "tours", "accommodations", "residences", "vehicles", "activities",
    "events", "media", "offers", "services", "visas", "transport", "blog", "taxonomy",
)

ROLE_RESOURCES = {
    # SUPER_ADMIN : superutilisateur Django (tous les droits), dérivé du rôle.
    User.Role.SUPER_ADMIN: {},
    # Tout sauf les paramètres système critiques (paramètres du site, paiements).
    User.Role.ADMIN: {
        **{resource: ALL for resource in CATALOG},
        "quotes": ALL, "contacts": ALL, "bookings": ALL, "reviews": ALL,
        "users": MANAGE, "site_settings": VIEW, "payments": VIEW,
    },
    # Contenu éditorial et catalogue touristique.
    User.Role.AGENT: {
        **{resource: VIEW for resource in CATALOG},
        "destinations": ALL, "tours": ALL, "accommodations": ALL, "activities": ALL,
        "blog": ALL, "media": ALL, "services": ALL, "visas": ALL, "transport": ALL,
        "taxonomy": ALL,
    },
    # Relation client : devis, réservations, messages.
    User.Role.COMMERCIAL: {
        **{resource: VIEW for resource in CATALOG},
        "quotes": MANAGE, "bookings": MANAGE, "contacts": MANAGE, "reviews": VIEW,
    },
    # Opérationnel : véhicules, résidences, événements, offres, avis.
    User.Role.GESTIONNAIRE: {
        **{resource: VIEW for resource in CATALOG},
        "vehicles": ALL, "residences": ALL, "events": ALL, "offers": ALL, "reviews": MANAGE,
        "bookings": VIEW,
    },
    User.Role.CLIENT: {},
}

DJANGO_ACTION = {"view": "view", "create": "add", "update": "change", "delete": "delete"}


def permissions_for_role(role):
    """Permissions Django ("app_label.codename") accordées à un rôle."""
    perms = set()
    for resource, actions in ROLE_RESOURCES.get(role, {}).items():
        for model in RESOURCES[resource]:
            app_label, model_name = model.split(".")
            for action in actions:
                perms.add(f"{app_label}.{DJANGO_ACTION[action]}_{model_name}")
    return perms


def group_name(role):
    return f"Rôle — {User.Role(role).label}"
