"""
Données personnelles (Phase 23, architecture § 11) : loi ivoirienne n° 2013-450
(ARTCI) et RGPD pour les visiteurs européens.

Chaque app qui stocke des données personnelles déclare une source dans son module
`privacy.py` (décorateur @register). Le registre sert à trois choses :

- droit d'accès : export JSON de tout ce qui concerne une adresse email ;
- droit à l'effacement : pour chaque enregistrement, suppression, anonymisation, ou
  conservation motivée (obligation comptable, dossier en cours) ;
- durées de conservation (PERSONAL_DATA_RETENTION_DAYS), appliquées chaque nuit
  par la tâche apply_retention_task et reprises dans la politique de confidentialité.

Outil de l'équipe : backoffice, liste des utilisateurs → « Données personnelles ».
"""
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import autodiscover_modules

logger = logging.getLogger(__name__)

DELETE, ANONYMIZE, KEEP = "delete", "anonymize", "keep"
DECISION_LABELS = {DELETE: "Supprimé", ANONYMIZE: "Anonymisé", KEEP: "Conservé"}
# Valeur des noms effacés : les statistiques (devis par mois…) restent justes.
ANONYMOUS = "Anonyme"

_sources: list["PersonalDataSource"] = []
_cleanups: list[Callable[[list], None]] = []
_discovered = False


class PersonalDataSource:
    """Données personnelles d'un modèle ; sous-classe déclarée dans <app>/privacy.py."""

    label = ""

    def find(self, email):
        """Enregistrements liés à cette adresse email (insensible à la casse)."""
        raise NotImplementedError

    def export(self, obj):
        """Données de l'enregistrement, pour le droit d'accès (valeurs sérialisables en JSON)."""
        raise NotImplementedError

    def decide(self, obj):
        """(DELETE | ANONYMIZE | KEEP, motif) en cas de demande d'effacement."""
        return DELETE, ""

    def delete(self, obj):
        obj.delete()

    def anonymize(self, obj):
        raise NotImplementedError

    def apply_retention(self, now):
        """Supprime ou anonymise ce qui a dépassé sa durée de conservation ; renvoie le nombre."""
        return 0

    def describe(self, obj):
        return str(obj)


def register(source_class):
    _sources.append(source_class())
    return source_class


def register_cleanup(function):
    """function([(modèle, pk)…] effacés) : nettoyage lié (notifications de l'équipe…)."""
    _cleanups.append(function)
    return function


def sources():
    global _discovered
    if not _discovered:
        autodiscover_modules("privacy")
        _discovered = True
    return list(_sources)


def retention_cutoff(key, now=None):
    return (now or timezone.now()) - timedelta(days=settings.PERSONAL_DATA_RETENTION_DAYS[key])


@dataclass
class Record:
    source: PersonalDataSource
    obj: object
    decision: str
    reason: str

    @property
    def label(self):
        return self.source.describe(self.obj)

    @property
    def decision_label(self):
        return DECISION_LABELS[self.decision]


def find_personal_data(email):
    """[(libellé de la source, [Record…])] pour une adresse email, sources vides exclues."""
    email = email.strip()
    found = []
    for source in sources():
        records = [Record(source, obj, *source.decide(obj)) for obj in source.find(email)]
        if records:
            found.append((source.label, records))
    return found


def export_personal_data(email):
    """Droit d'accès : {"email", "exported_at", "data": {source: [enregistrements]}}."""
    return {
        "email": email.strip(),
        "exported_at": timezone.now().isoformat(),
        "data": {label: [record.source.export(record.obj) for record in records]
                 for label, records in find_personal_data(email)},
    }


@transaction.atomic
def erase_personal_data(email):
    """Droit à l'effacement : applique la décision de chaque enregistrement ; renvoie le bilan."""
    summary, erased = [], []
    for label, records in find_personal_data(email):
        counts = dict.fromkeys(DECISION_LABELS, 0)
        for record in records:
            if record.decision == DELETE:
                erased.append((type(record.obj), record.obj.pk))
                record.source.delete(record.obj)
            elif record.decision == ANONYMIZE:
                erased.append((type(record.obj), record.obj.pk))
                record.source.anonymize(record.obj)
            counts[record.decision] += 1
        summary.append((label, counts))
    for cleanup in _cleanups:
        cleanup(erased)
    logger.info("Effacement des données personnelles demandé : %s enregistrement(s) traités.",
                len(erased))
    return summary


def apply_retention(now=None):
    """Durées de conservation : {source: nombre d'enregistrements supprimés ou anonymisés}."""
    now = now or timezone.now()
    report = {}
    for source in sources():
        with transaction.atomic():
            count = source.apply_retention(now)
        if count:
            report[source.label] = count
    return report
