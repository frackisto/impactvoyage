from django.db.models import Avg, Count, Q

from .models import Review


def approved_reviews(**target):
    """Avis publiés, éventuellement filtrés sur une page (destination=…, tour=…)."""
    return Review.objects.filter(status=Review.Status.APPROUVE, **target)


def featured_reviews(limit=6):
    return approved_reviews().filter(is_featured=True)[:limit]


def rating_summary(**target):
    """Note moyenne et nombre d'avis, pour l'affichage et le JSON-LD AggregateRating."""
    return approved_reviews(**target).aggregate(
        average=Avg("rating"), count=Count("id")
    )


def annotate_ratings(queryset, relation="reviews"):
    """
    Ajoute rating_avg et rating_count à une liste (circuits, hôtels...).
    distinct=True : le compte reste juste malgré les autres jointures (chambres, départs).
    """
    approved = Q(**{f"{relation}__status": Review.Status.APPROUVE})
    return queryset.annotate(
        rating_avg=Avg(f"{relation}__rating", filter=approved),
        rating_count=Count(relation, filter=approved, distinct=True),
    )


def pending_reviews():
    return Review.objects.filter(status=Review.Status.EN_ATTENTE)
