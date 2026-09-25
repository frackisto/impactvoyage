from rest_framework import serializers

from apps.core.serializers import CategorySerializer, TagSerializer

from .models import BlogPost


class BlogPostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id", "slug", "title", "excerpt", "cover_image", "cover_alt", "category",
            "author_name", "published_at", "reading_time",
        ]

    def get_author_name(self, obj):
        """Nom public uniquement : jamais l'email de l'auteur."""
        return obj.author.get_full_name() if obj.author else None


class BlogPostDetailSerializer(BlogPostListSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta(BlogPostListSerializer.Meta):
        fields = BlogPostListSerializer.Meta.fields + [
            "content", "tags", "seo_title", "seo_description",
        ]
