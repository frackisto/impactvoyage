from rest_framework import serializers

from apps.core.serializers import CategorySerializer, MediaAssetSerializer

from .models import MediaAlbum


class MediaItemSerializer(MediaAssetSerializer):
    title = serializers.CharField(read_only=True)
    is_featured = serializers.BooleanField(read_only=True)


class AlbumListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    items_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = MediaAlbum
        fields = ["id", "slug", "title", "cover", "category", "published_at", "items_count"]


class AlbumDetailSerializer(AlbumListSerializer):
    items = MediaItemSerializer(many=True, read_only=True)

    class Meta(AlbumListSerializer.Meta):
        fields = AlbumListSerializer.Meta.fields + ["description", "items"]
