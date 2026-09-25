from rest_framework import serializers

from apps.accommodations.models import Hotel
from apps.activities.models import Activity
from apps.core.serializers import HoneypotSerializerMixin
from apps.destinations.models import Destination
from apps.tours.models import Tour

from .models import REVIEW_TARGETS, Review

TARGET_QUERYSETS = {
    "destination": lambda: Destination.objects.published(),
    "tour": lambda: Tour.objects.published(),
    "hotel": lambda: Hotel.objects.published(),
    "activity": lambda: Activity.objects.published(),
}


class ReviewSerializer(serializers.ModelSerializer):
    """Avis publié : jamais l'email de l'auteur."""

    class Meta:
        model = Review
        fields = ["id", "author_name", "rating", "comment", "photo", "created_at"]


class ReviewCreateSerializer(HoneypotSerializerMixin, serializers.Serializer):
    """
    Dépôt d'un avis (CdC § 20). La page concernée est désignée par son type et
    son slug ; validated_data est prêt pour reviews.services.submit_review.
    """

    author_name = serializers.CharField(max_length=150)
    author_email = serializers.EmailField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(min_length=10, max_length=3000)
    photo = serializers.ImageField(required=False)
    target_type = serializers.ChoiceField(choices=REVIEW_TARGETS, required=False)
    target_slug = serializers.SlugField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        target_type = attrs.pop("target_type", None)
        target_slug = attrs.pop("target_slug", None)
        if bool(target_type) != bool(target_slug):
            raise serializers.ValidationError("Indiquez à la fois le type et le slug de la page.")
        if target_type:
            target = TARGET_QUERYSETS[target_type]().filter(slug=target_slug).first()
            if target is None:
                raise serializers.ValidationError({"target_slug": "Page introuvable."})
            attrs[target_type] = target
        return attrs
