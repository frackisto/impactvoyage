from .models import BlogPost


def post_list(category=None, tag=None):
    qs = BlogPost.objects.published().select_related("author", "category")
    if category:
        qs = qs.filter(category__slug=category)
    if tag:
        qs = qs.filter(tags__slug=tag)
    return qs.prefetch_related("tags")


def post_detail(slug):
    return (
        BlogPost.objects.published()
        .select_related("author", "category")
        .prefetch_related("tags")
        .get(slug=slug)
    )
