"""
Accueil du backoffice (UNFOLD["DASHBOARD_CALLBACK"]) : indicateurs, graphiques,
classements et listes « à traiter », chacun affiché seulement si le rôle peut
consulter la ressource concernée. Gabarit : templates/admin/index.html.
"""
import json

from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html

from apps.core.formatting import format_amount

from . import selectors, umami

# (clé de l'indicateur, libellé, permission, lien, clé du complément, texte du complément)
INDICATORS = (
    ("quotes_open", "Devis à traiter", "inquiries.view_quoterequest",
     ("inquiries_quoterequest", "status__in=NOUVELLE,EN_COURS"), "quotes_month", "reçu(s) ce mois-ci"),
    ("bookings_to_process", "Réservations à traiter", "bookings.view_booking",
     ("bookings_booking", "status__in=REQUESTED,PENDING"), "bookings_confirmed", "confirmée(s) à venir"),
    ("contacts_unread", "Messages non lus", "inquiries.view_contactmessage",
     ("inquiries_contactmessage", "status__exact=NOUVEAU"), None, None),
    ("reviews_pending", "Avis en attente", "reviews.view_review",
     ("reviews_review", "status__exact=EN_ATTENTE"), None, None),
    ("offers_active", "Offres en cours", "offers.view_offer",
     ("offers_offer", "is_active__exact=1"), None, None),
    ("tours", "Circuits publiés", "tours.view_tour",
     ("tours_tour", "is_published__exact=1"), None, None),
    ("destinations", "Destinations publiées", "destinations.view_destination",
     ("destinations_destination", "is_published__exact=1"), None, None),
    ("hotels", "Hôtels publiés", "accommodations.view_hotel",
     ("accommodations_hotel", "is_published__exact=1"), None, None),
    ("residences", "Résidences publiées", "accommodations.view_residence",
     ("accommodations_residence", "is_published__exact=1"), None, None),
    ("vehicles", "Véhicules publiés", "vehicles.view_vehicle",
     ("vehicles_vehicle", "is_published__exact=1"), None, None),
)


def environment_callback(request):
    """Pastille d'environnement à côté du compte (jamais affichée en production)."""
    if settings.DEBUG:
        return ["Développement", "warning"]
    if getattr(settings, "DEMO_DATA_ALLOWED", False):
        return ["Recette", "info"]
    return None


def _changelist(route, query=""):
    url = reverse(f"admin:{route}_changelist")
    return f"{url}?{query}" if query else url


def _link(route, pk, text):
    return format_html('<a href="{}" class="text-primary-600">{}</a>',
                       reverse(f"admin:{route}_change", args=[pk]), text)


def _indicators(user, values):
    cards = []
    for key, label, perm, (route, query), extra_key, extra_label in INDICATORS:
        if not user.has_perm(perm):
            continue
        cards.append({
            "label": label,
            "value": values[key],
            "url": _changelist(route, query),
            "footer": f"{values[extra_key]} {extra_label}" if extra_key else "",
        })
    return cards


def _bar_chart(labels, values, label):
    return json.dumps({
        "labels": labels,
        "datasets": [{
            "label": label,
            "data": values,
            "backgroundColor": "var(--color-primary-600)",
            "maxBarThickness": 24,
        }],
    })


# Options Chart.js complètes (unfold les remplace au lieu de les fusionner) : style
# d'unfold, graduations entières puisqu'on compte des demandes.
BAR_CHART_OPTIONS = json.dumps({
    "animation": False,
    "responsive": True,
    "maintainAspectRatio": False,
    "datasets": {"bar": {"borderRadius": 12, "borderSkipped": "middle"}},
    "plugins": {"legend": {"display": False}, "tooltip": {"enabled": True}},
    "scales": {
        "x": {"border": {"width": 0}, "grid": {"display": False}, "ticks": {"color": "#9ca3af"}},
        "y": {"beginAtZero": True, "border": {"width": 0}, "grid": {"tickWidth": 0},
              "ticks": {"color": "#9ca3af", "precision": 0}},
    },
})


def _charts(user, stats):
    charts = []
    series = (
        ("inquiries.view_quoterequest", "Demandes de devis par mois", "Devis", "quotes_by_month"),
        ("bookings.view_booking", "Réservations par mois", "Réservations", "bookings_by_month"),
    )
    for perm, title, label, key in series:
        if user.has_perm(perm):
            values = stats[key]
            charts.append({
                "title": title,
                "data": _bar_chart(stats["months"], values, label),
                "options": BAR_CHART_OPTIONS,
                "summary": f"{sum(values)} sur 12 mois, dont {values[-1]} ce mois-ci.",
            })
    return charts


def _rankings(user, stats):
    rankings = []
    if user.has_perm("destinations.view_destination"):
        rankings.append({
            "title": "Destinations populaires",
            "table": {
                "headers": ["Destination", "Réservations", "Vues"],
                "rows": [[_link("destinations_destination", d["pk"], d["name"]), d["bookings"],
                          d["view_count"]] for d in stats["popular_destinations"]],
            },
        })
    if user.has_perm("tours.view_tour"):
        rankings.append({
            "title": "Circuits populaires",
            "table": {
                "headers": ["Circuit", "Réservations", "Vues"],
                "rows": [[_link("tours_tour", t["pk"], t["title"]), t["bookings"], t["view_count"]]
                         for t in stats["popular_tours"]],
            },
        })
    return rankings


def _todo(user):
    todo = []
    if user.has_perm("bookings.view_booking"):
        todo.append({
            "title": "Réservations à traiter",
            "url": _changelist("bookings_booking", "status__in=REQUESTED,PENDING"),
            "table": {
                "headers": ["Référence", "Client", "Statut", "Total"],
                "rows": [[_link("bookings_booking", b.pk, b.reference), b.contact_name,
                          b.get_status_display(), format_amount(b.total_amount, b.currency)]
                         for b in selectors.bookings_to_process()],
            },
        })
    if user.has_perm("inquiries.view_quoterequest"):
        todo.append({
            "title": "Devis à traiter",
            "url": _changelist("inquiries_quoterequest", "status__in=NOUVELLE,EN_COURS"),
            "table": {
                "headers": ["Référence", "Client", "Destination", "Assigné à"],
                "rows": [[_link("inquiries_quoterequest", q.pk, q.reference),
                          f"{q.first_name} {q.last_name}",
                          q.destination_text or (q.destination.name if q.destination else "—"),
                          str(q.assigned_to) if q.assigned_to else "—"]
                         for q in selectors.quotes_to_process()],
            },
        })
    return todo


def dashboard_callback(request, context):
    user = request.user
    stats = selectors.dashboard_stats()
    context.update({
        "title": "Tableau de bord",
        "indicators": _indicators(user, stats["indicators"]),
        "charts": _charts(user, stats),
        "rankings": _rankings(user, stats),
        "todo": _todo(user),
        "notifications": selectors.unread_notifications(user),
        "notifications_url": _changelist("notifications_notification", "is_read__exact=0"),
        "visitors": umami.visitor_stats(),
        "stats_computed_at": stats["computed_at"],
    })
    return context
