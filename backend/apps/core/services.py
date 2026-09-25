"""Services transverses : devises et taux de change (architecture § 12)."""
import json
import logging
from decimal import ROUND_HALF_UP, Decimal
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .exceptions import BusinessError
from .models import ExchangeRate

logger = logging.getLogger(__name__)

RATES_CACHE_KEY = "exchange_rates"
# Nombre de décimales affichées par devise (le FCFA n'a pas de centimes).
DISPLAY_DECIMALS = {"XOF": 0, "EUR": 2, "USD": 2, "GBP": 2}


def get_rates():
    """Taux {devise: taux depuis XOF}, mis en cache jusqu'à la prochaine mise à jour."""
    rates = cache.get(RATES_CACHE_KEY)
    if rates is None:
        rates = {r.currency: r.rate_from_xof for r in ExchangeRate.objects.all()}
        rates[settings.DEFAULT_CURRENCY] = Decimal("1")
        cache.set(RATES_CACHE_KEY, rates, timeout=None)
    return rates


def convert_from_xof(amount, currency):
    """Convertit un montant FCFA dans une devise d'affichage, arrondi pour l'affichage."""
    if currency == settings.DEFAULT_CURRENCY:
        return Decimal(amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    rate = get_rates().get(currency)
    if rate is None:
        raise BusinessError(f"Devise non disponible : {currency}.", code="unknown_currency")
    decimals = DISPLAY_DECIMALS.get(currency, 2)
    return (Decimal(amount) * rate).quantize(
        Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP
    )


def fetch_eur_rates(symbols):
    """Taux EUR → devises (BCE via l'API Frankfurter, sans clé)."""
    url = f"{settings.EXCHANGE_RATES_API_URL}?base=EUR&symbols={','.join(symbols)}"
    # User-Agent explicite : l'agent par défaut « Python-urllib » est bloqué (Cloudflare 1010).
    request = Request(
        url, headers={"User-Agent": "impactvoyage/1.0", "Accept": "application/json"}
    )
    with urlopen(request, timeout=10) as response:  # noqa: S310 (URL fixée par la config)
        payload = json.load(response)
    return {code: Decimal(str(value)) for code, value in payload["rates"].items()}


@transaction.atomic
def update_exchange_rates(fetch=fetch_eur_rates):
    """
    Met à jour les taux XOF → EUR/USD/GBP. Le FCFA est arrimé à l'euro
    (1 EUR = 655,957 XOF) : seuls les taux EUR → USD/GBP sont récupérés.
    """
    xof_per_eur = settings.XOF_PER_EUR
    others = [c for c in settings.DISPLAY_CURRENCIES if c not in ("XOF", "EUR")]
    eur_rates = fetch(others)
    rates = {"EUR": Decimal("1") / xof_per_eur}
    for code in others:
        rates[code] = eur_rates[code] / xof_per_eur
    now = timezone.now()
    for code, rate in rates.items():
        ExchangeRate.objects.update_or_create(
            currency=code,
            defaults={"rate_from_xof": rate.quantize(Decimal("1e-10")), "fetched_at": now},
        )
    transaction.on_commit(lambda: cache.delete(RATES_CACHE_KEY))
    logger.info("Taux de change mis à jour : %s", ", ".join(sorted(rates)))
    return rates
