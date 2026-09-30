"""
Recherche globale (architecture § 5, CdC § 7) dans les contenus publiés, sans
table dédiée : pg_trgm (tolérance aux fautes de frappe) et unaccent (« Dubai »
trouve « Dubaï »).

Chaque mot de la requête doit ressembler à un mot du document de l'objet
(titre, accroche, destination... dans toutes les langues) ; le score favorise
les correspondances dans le titre.
"""
import builtins
import re
import unicodedata
from dataclasses import dataclass

from django.conf import settings
from django.contrib.postgres.search import TrigramWordSimilarity
from django.db.models import F, FloatField, Func, Min, Q, TextField, Value
from django.db.models.functions import Coalesce, Concat, Lower
from modeltranslation.translator import NotRegistered, translator
from modeltranslation.utils import build_localized_fieldname

from apps.accommodations.models import Hotel, Residence
from apps.activities.models import Activity
from apps.destinations.models import Destination
from apps.events.models import Event
from apps.tours.models import Tour
from apps.vehicles.models import Vehicle

# Ressemblance minimale d'un mot de la requête avec un mot du document (0 à 1) :
# « dubay » ≈ « dubai » (0,67) passe, « chien » ≈ « chine » (0,5) non.
TERM_THRESHOLD = 0.6
MAX_TERMS = 6
STOP_WORDS = {
    "de", "du", "des", "la", "le", "les", "en", "et", "au", "aux", "un", "une", "pour", "avec",
    "sur", "dans", "the", "of", "and", "in", "to", "for", "with", "on", "at",
}


class Unaccent(Func):
    function = "UNACCENT"
    output_field = TextField()


@dataclass(frozen=True)
class SearchTarget:
    """Type de contenu cherchable : champs du document, titre, prix et unité."""

    type: str
    model: builtins.type  # « type » désigne ici le champ ci-dessus
    fields: tuple
    title_field: str
    price_field: str | None = None
    price_unit: str | None = None
    destination_field: str | None = "destination"
    # Champs du titre (score) quand il ne se réduit pas à title_field (véhicule : marque + modèle).
    title_paths: tuple = ()

    def queryset(self):
        qs = self.model.objects.published()
        if self.destination_field:
            qs = qs.select_related(self.destination_field)
        if self.type == "hotel":
            qs = qs.annotate(price_from=Min("rooms__base_price", filter=Q(rooms__is_active=True)))
        return qs


TARGETS = [
    SearchTarget("destination", Destination, ("name", "city", "short_description", "attractions"), "name",
                 destination_field=None),
    SearchTarget("tour", Tour, ("title", "short_description", "destination__name", "theme__name"), "title",
                 "base_price", "person"),
    SearchTarget("hotel", Hotel, ("name", "short_description", "destination__name", "address"), "name",
                 "price_from", "night"),
    SearchTarget("residence", Residence,
                 ("name", "short_description", "destination__name", "address"), "name",
                 "base_price", "night"),
    SearchTarget("vehicle", Vehicle, ("brand", "model", "category"), "model", "base_price", "day",
                 title_paths=("brand", "model"),
                 destination_field=None),
    SearchTarget("activity", Activity, ("title", "short_description", "destination__name", "category__name"),
                 "title", "base_price", "person"),
    SearchTarget("event", Event, ("title", "short_description", "location", "destination__name"), "title"),
]
TYPES = [target.type for target in TARGETS]


def normalize(text):
    """Minuscules, sans accents : « Dubaï » → « dubai »."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def query_terms(query):
    """Mots significatifs de la requête (2 caractères au moins, hors mots vides)."""
    words = re.findall(r"\w+", normalize(query))
    return [w for w in words if len(w) >= 2 and w not in STOP_WORDS][:MAX_TERMS]


def columns(model, path):
    """
    Colonnes réelles d'un champ, dans toutes les langues pour un champ traduit
    (django-modeltranslation) : « destination__name » → name_fr et name_en.
    """
    *relations, field = path.split("__")
    target = model
    for relation in relations:
        target = target._meta.get_field(relation).related_model
    try:
        translated = field in translator.get_options_for_model(target).fields
    except NotRegistered:
        translated = False
    prefix = "".join(f"{relation}__" for relation in relations)
    if not translated:
        return [path]
    return [prefix + build_localized_fieldname(field, code) for code, _ in settings.LANGUAGES]


def document(model, paths):
    """Texte cherchable : champs concaténés, en minuscules et sans accents."""
    parts = []
    for path in paths:
        for column in columns(model, path):
            parts += [Coalesce(F(column), Value(""), output_field=TextField()), Value(" ")]
    return Unaccent(Lower(Concat(*parts, output_field=TextField())))


def search(query, types=None, destination=None):
    """
    Résultats par type : {type: (SearchTarget, queryset trié par score décroissant)}.
    Un type sans lien avec une destination est ignoré quand `destination` est donné.
    """
    terms = query_terms(query)
    if not terms:
        return {}
    phrase = " ".join(terms)
    results = {}
    for target in TARGETS:
        if types and target.type not in types:
            continue
        if destination and not target.destination_field and target.type != "destination":
            continue
        qs = target.queryset().annotate(
            _doc=document(target.model, target.fields),
            _title=document(target.model, target.title_paths or (target.title_field,)),
        )
        if destination:
            qs = qs.filter(slug=destination) if target.type == "destination" else qs.filter(
                **{f"{target.destination_field}__slug": destination}
            )
        score = Value(0.0, output_field=FloatField())
        for index, term in enumerate(terms):
            qs = qs.annotate(**{f"_t{index}": TrigramWordSimilarity(term, "_doc")}).filter(
                **{f"_t{index}__gte": TERM_THRESHOLD}
            )
            score = score + F(f"_t{index}")
        qs = qs.annotate(score=score + TrigramWordSimilarity(phrase, "_title")).order_by("-score", "pk")
        results[target.type] = (target, qs)
    return results
