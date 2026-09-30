"""
Briques de sérialisation partagées.

Les champs traduits (title, description...) sont lus dans la langue de la
requête (Accept-Language, via LocaleMiddleware) avec repli sur le français :
les serializers n'ont rien de particulier à faire.
"""
import contextlib
from decimal import Decimal
from operator import attrgetter

from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings

from .captcha import verify_captcha
from .exceptions import BusinessError
from .models import Category, ExchangeRate, SiteSettings, Tag
from .services import convert_from_xof
from .throttling import client_ip

CAPTCHA_ERROR = "La vérification anti-robot a échoué ou a expiré. Réessayez."


def get_display_currency(request):
    """Devise d'affichage demandée (?currency=EUR ou en-tête X-Currency), sinon FCFA."""
    if request is None:
        return settings.DEFAULT_CURRENCY
    code = (
        request.query_params.get("currency")
        if hasattr(request, "query_params")
        else request.GET.get("currency")
    ) or request.headers.get("X-Currency", "")
    code = code.upper()
    return code if code in settings.DISPLAY_CURRENCIES else settings.DEFAULT_CURRENCY


def money_repr(amount, currency, request=None):
    """
    {"amount": "150000.00", "currency": "XOF"}, plus "display" converti si le
    visiteur a choisi une autre devise d'affichage (prix stockés en FCFA).
    """
    if amount is None:
        return None
    currency = currency or settings.DEFAULT_CURRENCY
    data = {"amount": f"{Decimal(amount):.2f}", "currency": currency}
    display = get_display_currency(request)
    if display != currency and currency == settings.DEFAULT_CURRENCY:
        with contextlib.suppress(BusinessError):  # taux indisponible : prix d'origine seul
            data["display"] = {
                "amount": str(convert_from_xof(amount, display)),
                "currency": display,
            }
    return data


class DisplayAmountSerializer(serializers.Serializer):
    amount = serializers.CharField()
    currency = serializers.CharField()


class MoneySerializer(serializers.Serializer):
    """Schéma OpenAPI d'un montant (voir money_repr)."""

    amount = serializers.CharField(help_text="Montant décimal, ex. « 150000.00 »")
    currency = serializers.CharField(help_text="Code ISO 4217, ex. « XOF »")
    display = DisplayAmountSerializer(required=False, help_text="Conversion d'affichage")


class RatingSummarySerializer(serializers.Serializer):
    average = serializers.FloatField(allow_null=True)
    count = serializers.IntegerField()


@extend_schema_field(MoneySerializer(allow_null=True))
class MoneyField(serializers.Field):
    """
    Montant en lecture seule (voir money_repr). `amount` et `currency` sont des
    chemins d'attributs (pointés autorisés) ; sans attribut devise : FCFA.
    """

    def __init__(self, amount, currency="currency", **kwargs):
        kwargs.update(source="*", read_only=True)
        super().__init__(**kwargs)
        self.amount_path = amount
        self.currency_path = currency

    def _get(self, obj, path):
        try:
            return attrgetter(path)(obj)
        except AttributeError:
            return None

    def to_representation(self, obj):
        return money_repr(
            self._get(obj, self.amount_path),
            self._get(obj, self.currency_path),
            self.context.get("request"),
        )


@extend_schema_field({"type": "array", "items": {"type": "string"}})
class LinesField(serializers.Field):
    """Texte « un élément par ligne » (attractions, inclusions...) exposé en liste."""

    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        return [line.strip(" -•\t") for line in (value or "").splitlines() if line.strip(" -•\t")]


class HoneypotSerializerMixin(serializers.Serializer):
    """
    Anti-spam des formulaires publics (CdC § 19, § 29) :
    - champ `website` invisible dans le formulaire : un robot qui le remplit est rejeté ;
    - jeton Cloudflare Turnstile `captcha_token` (Phase 23, apps/core/captcha.py),
      vérifié en dernier, une fois toutes les autres données valides : un jeton ne
      sert qu'une fois, il n'est pas gaspillé par une simple erreur de saisie.
    """

    website = serializers.CharField(required=False, allow_blank=True, write_only=True)
    captcha_token = serializers.CharField(required=False, allow_blank=True, write_only=True,
                                          help_text="Jeton du widget Cloudflare Turnstile")

    def run_validation(self, data=empty):
        value = super().run_validation(data)
        request = self.context.get("request")
        ip = client_ip(request) if request is not None else None
        if not verify_captcha(value.pop("captcha_token", ""), ip):
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [CAPTCHA_ERROR]}, code="captcha_invalid"
            )
        return value

    def validate_website(self, value):
        if value:
            raise serializers.ValidationError("Requête refusée.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs.pop("website", None)
        return attrs


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "kind"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "slug"]


class GalleryImageSerializer(serializers.Serializer):
    """Photo de galerie : URL absolue, dimensions (anti-CLS) et texte alternatif."""

    id = serializers.IntegerField(read_only=True)
    image = serializers.ImageField(read_only=True)
    width = serializers.IntegerField(read_only=True)
    height = serializers.IntegerField(read_only=True)
    alt_text = serializers.CharField(read_only=True)


class MediaAssetSerializer(GalleryImageSerializer):
    type = serializers.CharField(read_only=True)
    video_url = serializers.URLField(read_only=True)


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            "agency_name", "slogan", "hero_subtitle", "hero_image", "hero_video_url",
            "phone", "email", "whatsapp", "address", "opening_hours", "social_links",
            "latitude", "longitude", "about_content",
        ]


class ExchangeRateSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_currency_display", read_only=True)

    class Meta:
        model = ExchangeRate
        fields = ["currency", "label", "rate_from_xof", "fetched_at"]


class AvailabilitySerializer(serializers.Serializer):
    """Réponse des actions /availability/ (véhicules, résidences)."""

    available = serializers.BooleanField()
    booked_periods = serializers.ListField(child=serializers.ListField(child=serializers.DateField()))
