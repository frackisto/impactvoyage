from django.contrib import admin
from unfold.decorators import display

from apps.core.admin import MediaAssetInline, PublishableAdminMixin, TranslatedAdmin, image_preview

from .models import MediaAlbum, MediaItem


class MediaItemInline(MediaAssetInline):
    model = MediaItem
    fields = ("preview", "type", "image", "video_url", "title", "alt_text", "is_featured", "order")


@admin.register(MediaAlbum)
class MediaAlbumAdmin(PublishableAdminMixin, TranslatedAdmin):
    list_display = ("cover_preview", "title", "category", "published_at", "items_count",
                    "is_published")
    list_display_links = ("cover_preview", "title")
    list_filter = ("category", "is_published")
    search_fields = ("title",)
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("event", "tour")
    inlines = (MediaItemInline,)
    fields = ("title", "slug", "description", "cover", "category", "event", "tour",
              "published_at", "is_published")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items")

    @display(description="couverture")
    def cover_preview(self, obj):
        return image_preview(obj.cover, obj.title, height=40)

    @display(description="médias")
    def items_count(self, obj):
        return len(obj.items.all())
