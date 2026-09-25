from .models import Offer


def active_offers():
    return Offer.objects.currently_active().select_related(
        "destination", "tour", "hotel", "residence", "vehicle", "activity"
    )


def promo_price_for(target):
    """
    Prix promotionnel actif le plus bas pour un circuit (par voyageur), une
    résidence (par nuit), un véhicule (par jour) ou une activité (par personne).
    Les offres « hôtel » sont indicatives : le prix dépend de la chambre.
    """
    field = target._meta.model_name
    if field not in ("tour", "residence", "vehicle", "activity"):
        return None
    offer = (
        Offer.objects.currently_active()
        .filter(**{field: target})
        .order_by("promo_price")
        .only("promo_price")
        .first()
    )
    return offer.promo_price if offer else None
