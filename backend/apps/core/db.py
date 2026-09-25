"""Outils base de données partagés (contraintes, fonctions PostgreSQL)."""
from itertools import combinations

from django.contrib.postgres.fields import DateRangeField
from django.db.models import Func, Q


class DateRange(Func):
    """daterange(start, end, bounds) PostgreSQL, pour les ExclusionConstraint."""

    function = "DATERANGE"
    output_field = DateRangeField()


def at_most_one(*fields):
    """Q vrai si au plus une des FK données est renseignée."""
    q = Q()
    for a, b in combinations(fields, 2):
        q &= ~Q(**{f"{a}__isnull": False, f"{b}__isnull": False})
    return q


def exactly_one(*fields):
    """Q vrai si exactement une des FK données est renseignée."""
    any_set = Q()
    for field in fields:
        any_set |= Q(**{f"{field}__isnull": False})
    return at_most_one(*fields) & any_set
