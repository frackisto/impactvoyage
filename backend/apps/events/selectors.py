from .models import Event


def event_list(category=None, year=None):
    qs = Event.objects.published().select_related("destination")
    if category:
        qs = qs.filter(category=category)
    if year:
        qs = qs.filter(date__year=year)
    return qs


def event_detail(slug):
    return (
        Event.objects.published()
        .select_related("destination")
        .prefetch_related("media", "albums__items")
        .get(slug=slug)
    )
