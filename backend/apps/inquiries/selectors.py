from .models import ContactMessage, QuoteRequest


def quote_queryset():
    return QuoteRequest.objects.select_related(
        "destination", "assigned_to", "source_tour", "source_offer"
    ).prefetch_related("activities")


def quotes_for_staff(status=None, assigned_to=None):
    qs = quote_queryset()
    if status:
        qs = qs.filter(status=status)
    if assigned_to:
        qs = qs.filter(assigned_to=assigned_to)
    return qs


def quotes_for_user(user):
    """Espace client : devis envoyés avec l'email du compte."""
    return quote_queryset().filter(email__iexact=user.email)


def unread_contact_messages():
    return ContactMessage.objects.filter(status=ContactMessage.Status.NOUVEAU)
