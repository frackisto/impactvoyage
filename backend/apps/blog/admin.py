from django import forms
from django.contrib import admin
from django.utils import timezone
from unfold.decorators import display

from apps.core.admin import CoverPreviewMixin, TranslatedAdmin

from .models import BlogPost

STATUS_LABELS = {BlogPost.Status.BROUILLON: "default", BlogPost.Status.PUBLIE: "success"}


class BlogPostForm(forms.ModelForm):
    def clean(self):
        data = super().clean()
        # Un article publié a une date de publication : maintenant, si elle est vide.
        if data.get("status") == BlogPost.Status.PUBLIE and not data.get("published_at"):
            data["published_at"] = timezone.now()
        return data


@admin.register(BlogPost)
class BlogPostAdmin(CoverPreviewMixin, TranslatedAdmin):
    form = BlogPostForm
    list_display = ("cover_preview", "title", "category", "author", "status_label",
                    "published_at", "reading_time")
    list_display_links = ("cover_preview", "title")
    list_filter = ("status", "category", "tags")
    search_fields = ("title", "excerpt")
    list_select_related = ("category", "author")
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("reading_time", "created", "updated")
    actions = ("publish_now", "back_to_draft")
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "tags", "author", "status",
                           "published_at")}),
        ("Contenu", {"fields": ("excerpt", "content", "reading_time")}),
        ("Référencement", {"fields": ("seo_title", "seo_description")}),
        ("Image principale", {"fields": ("cover_image", "cover_alt")}),
        ("Historique", {"fields": ("created", "updated")}),
    )

    def get_changeform_initial_data(self, request):
        return {"author": request.user.pk, **super().get_changeform_initial_data(request)}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            from django.contrib.auth import get_user_model

            kwargs["queryset"] = get_user_model().objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @display(description="statut", ordering="status", label=STATUS_LABELS)
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @admin.action(description="Publier maintenant", permissions=["change"])
    def publish_now(self, request, queryset):
        now = timezone.now()
        drafts = queryset.exclude(status=BlogPost.Status.PUBLIE)
        undated = drafts.filter(published_at__isnull=True).update(
            status=BlogPost.Status.PUBLIE, published_at=now)
        dated = drafts.update(status=BlogPost.Status.PUBLIE)
        self.message_user(request, f"{undated + dated} article(s) publié(s).")

    @admin.action(description="Repasser en brouillon", permissions=["change"])
    def back_to_draft(self, request, queryset):
        count = queryset.update(status=BlogPost.Status.BROUILLON)
        self.message_user(request, f"{count} article(s) repassé(s) en brouillon.")
