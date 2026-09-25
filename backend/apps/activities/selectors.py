from .models import Activity


def activity_list(destination=None, category=None, max_price=None, max_hours=None):
    qs = Activity.objects.published().select_related("destination", "category")
    if destination:
        qs = qs.filter(destination__slug=destination)
    if category:
        qs = qs.filter(category__slug=category)
    if max_price is not None:
        qs = qs.filter(base_price__lte=max_price)
    if max_hours:
        qs = qs.filter(duration_hours__lte=max_hours)
    return qs


def activity_detail(slug):
    return (
        Activity.objects.published()
        .select_related("destination", "category")
        .prefetch_related("images")
        .get(slug=slug)
    )
