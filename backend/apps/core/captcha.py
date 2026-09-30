"""
Anti-spam des formulaires publics (CdC § 29, Phase 23) : Cloudflare Turnstile.

Le navigateur obtient un jeton du widget Turnstile (frontend/components/common/
turnstile.tsx) et l'envoie avec le formulaire (`captcha_token`) ; Django le fait
valider par Cloudflare avant d'enregistrer quoi que ce soit. Un jeton ne sert
qu'une fois et expire au bout de 5 minutes.

Clé secrète vide (TURNSTILE_SECRET_KEY) : vérification désactivée. Si Cloudflare
est injoignable, la demande est acceptée (le champ piège et la limitation de
débit restent actifs) : une panne chez Cloudflare ne doit pas faire perdre de
demande de client.
"""
import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5


def captcha_enabled():
    return bool(settings.TURNSTILE_SECRET_KEY)


def verify_captcha(token, remote_ip=None):
    """Vrai si le jeton Turnstile est valide (ou si la vérification est désactivée)."""
    if not captcha_enabled():
        return True
    if not token:
        return False
    payload = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip
    request = Request(settings.TURNSTILE_VERIFY_URL, data=urlencode(payload).encode(),
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310 (URL fixe)
            result = json.load(response)
    except (URLError, TimeoutError, ValueError) as exc:
        logger.warning("Turnstile injoignable, formulaire accepté sans vérification : %s", exc)
        return True
    if not result.get("success"):
        errors = result.get("error-codes") or []
        # Clé secrète erronée : tous les formulaires seraient refusés, à corriger d'urgence.
        log = logger.error if any("secret" in code for code in errors) else logger.info
        log("Jeton Turnstile refusé : %s", errors)
        return False
    return True
