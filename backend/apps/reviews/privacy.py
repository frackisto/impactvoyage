"""Données personnelles des avis clients (apps/core/privacy.py)."""
from django.db.models import Q

from apps.core import privacy

from .models import REVIEW_TARGETS, Review


def delete_reviews(queryset):
    """Supprime les avis et leur photo (le fichier ne disparaît pas avec la ligne)."""
    count = 0
    for review in queryset:
        if review.photo:
            review.photo.delete(save=False)
        review.delete()
        count += 1
    return count


@privacy.register
class Reviews(privacy.PersonalDataSource):
    label = "Avis"

    def find(self, email):
        return (Review.objects.filter(Q(author_email__iexact=email) | Q(user__email__iexact=email))
                .order_by("created_at"))

    def export(self, obj):
        return {
            "date": obj.created_at.isoformat(), "nom": obj.author_name,
            "email": obj.author_email, "note": obj.rating, "commentaire": obj.comment,
            "photo": obj.photo.name if obj.photo else "",
            "sujet": str(next((t for t in map(obj.__getattribute__, REVIEW_TARGETS) if t),
                              "L'agence")),
            "statut": obj.get_status_display(),
        }

    def describe(self, obj):
        return f"{obj.created_at:%d/%m/%Y} — {obj.rating}/5 ({obj.get_status_display()})"

    def delete(self, obj):
        delete_reviews([obj])

    def apply_retention(self, now):
        cutoff = privacy.retention_cutoff("rejected_reviews", now)
        return delete_reviews(Review.objects.filter(status=Review.Status.REFUSE,
                                                    updated_at__lt=cutoff))
