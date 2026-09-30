"""
Limitation de débit (CdC § 29) adaptée au rendu des pages par le serveur Next.js.

Toutes les pages sont rendues par Next.js : sans précaution, Django verrait une
seule adresse IP pour tous les visiteurs et les limites (120 lectures/min,
10 connexions/min...) s'appliqueraient au site entier. Le serveur Next.js
s'identifie donc avec un secret partagé (en-tête X-Frontend-Secret) :

- avec X-Client-IP (requêtes propres à un visiteur : connexion, formulaires,
  disponibilités), la limite s'applique à l'adresse réelle du visiteur ;
- sans X-Client-IP, une lecture (pages publiques mises en cache par Next.js)
  n'est pas limitée ici : le trafic des pages est limité en amont (Nginx) ;
  une écriture reste toujours limitée.

Sans secret valide, l'adresse est REMOTE_ADDR (X-Forwarded-For n'est pris en
compte que derrière un proxy déclaré, réglage REST_FRAMEWORK["NUM_PROXIES"]).
"""
import hmac
import ipaddress

from django.conf import settings
from rest_framework import throttling
from rest_framework.permissions import SAFE_METHODS

SECRET_HEADER = "HTTP_X_FRONTEND_SECRET"
CLIENT_IP_HEADER = "HTTP_X_CLIENT_IP"


def is_trusted_frontend(request):
    """Vrai si la requête vient du serveur Next.js (secret partagé, comparaison à temps constant)."""
    secret = getattr(settings, "FRONTEND_SHARED_SECRET", "")
    sent = request.META.get(SECRET_HEADER, "")
    return bool(secret) and hmac.compare_digest(sent.encode(), secret.encode())


def forwarded_client_ip(request):
    """Adresse du visiteur transmise par le serveur Next.js, si elle est valide."""
    try:
        return str(ipaddress.ip_address(request.META.get(CLIENT_IP_HEADER, "").strip()))
    except ValueError:
        return None


class FrontendAwareThrottleMixin:
    def get_ident(self, request):
        if is_trusted_frontend(request) and (client := forwarded_client_ip(request)):
            return client
        return super().get_ident(request)

    def allow_request(self, request, view):
        # Lectures seulement : une écriture (connexion, devis...) reste toujours limitée.
        if (request.method in SAFE_METHODS and is_trusted_frontend(request)
                and not forwarded_client_ip(request)):
            return True
        return super().allow_request(request, view)


class AnonRateThrottle(FrontendAwareThrottleMixin, throttling.AnonRateThrottle):
    pass


class UserRateThrottle(FrontendAwareThrottleMixin, throttling.UserRateThrottle):
    pass


class ScopedRateThrottle(FrontendAwareThrottleMixin, throttling.ScopedRateThrottle):
    pass
