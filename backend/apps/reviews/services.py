"""Avis clients : dépôt puis modération dans l'administration (CdC § 20)."""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.exceptions import InvalidTransition
from apps.core.validators import strip_image_metadata, validate_image_content
from apps.notifications.models import Notification
from apps.notifications.services import admin_path, notify_staff

from .models import Review


@transaction.atomic
def submit_review(*, author_name, author_email, rating, comment, user=None, photo=None, **target):
    """Dépose un avis en attente de validation ; target = destination|tour|hotel|activity."""
    if photo:
        # Contenu contrôlé avant tout décodage complet, puis métadonnées (GPS…) retirées.
        try:
            validate_image_content(photo)
        except ValidationError as exc:
            raise ValidationError({"photo": exc.error_list}) from exc
        photo = strip_image_metadata(photo)
    review = Review(
        author_name=author_name,
        author_email=author_email,
        rating=rating,
        comment=comment,
        user=user,
        photo=photo or "",
        **target,
    )
    review.full_clean()
    review.save()
    notify_staff(
        Notification.Event.REVIEW_SUBMITTED,
        f"Nouvel avis à modérer ({rating}/5)",
        f"{author_name} : {comment[:300]}",
        link=admin_path(review),
        related_object=review,
        details=[("Auteur", f"{author_name}\n{author_email}"), ("Note", f"{rating}/5"),
                 ("Sujet", str(next((v for v in target.values() if v), "L'agence"))),
                 ("Commentaire", comment)],
    )
    return review


def _moderate(review, status, featured=None):
    if review.status == status:
        raise InvalidTransition("Cet avis a déjà ce statut.")
    review.status = status
    fields = ["status", "updated_at"]
    if featured is not None:
        review.is_featured = featured
        fields.append("is_featured")
    review.save(update_fields=fields)
    return review


def approve_review(review, featured=False):
    return _moderate(review, Review.Status.APPROUVE, featured)


def reject_review(review):
    return _moderate(review, Review.Status.REFUSE, featured=False)
