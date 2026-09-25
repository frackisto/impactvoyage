from django.db.models import Count

from .models import MediaAlbum


def album_list(category=None):
    qs = (
        MediaAlbum.objects.published()
        .select_related("category", "event", "tour")
        .annotate(items_count=Count("items"))
    )
    if category:
        qs = qs.filter(category__slug=category)
    return qs


def album_detail(slug):
    return MediaAlbum.objects.published().prefetch_related("items").get(slug=slug)
