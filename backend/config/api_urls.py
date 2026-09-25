"""
Point d'entrée unique de l'API v1.
Les routes des apps métier (destinations, tours, hôtels...) seront
ajoutées ici au fur et à mesure des phases suivantes du projet.
"""
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    return JsonResponse({"status": "ok", "service": "voyage-api"})


urlpatterns = [
    path("health/", health_check, name="health-check"),
    # path("destinations/", include("apps.destinations.urls")),
    # path("tours/", include("apps.tours.urls")),
    # ... ajoutés progressivement dans les phases suivantes
]
