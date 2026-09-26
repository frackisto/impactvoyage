from rest_framework import serializers

from apps.core.serializers import MoneySerializer, money_repr

from .selectors import TYPES


class SearchParamsSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=100, help_text="Mots recherchés (fautes et accents tolérés)")
    type = serializers.CharField(required=False, help_text=f"Types séparés par des virgules : {', '.join(TYPES)}")
    destination = serializers.SlugField(required=False)
    limit = serializers.IntegerField(min_value=1, max_value=48, default=24)

    def validate_type(self, value):
        types = [t.strip() for t in value.split(",") if t.strip()]
        unknown = set(types) - set(TYPES)
        if unknown:
            raise serializers.ValidationError(f"Types inconnus : {', '.join(sorted(unknown))}.")
        return types


class SearchResultSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=TYPES)
    slug = serializers.CharField()
    title = serializers.CharField()
    excerpt = serializers.CharField(allow_blank=True)
    image = serializers.CharField(allow_null=True, help_text="URL de l'image principale")
    image_alt = serializers.CharField(allow_blank=True)
    context = serializers.CharField(allow_blank=True, help_text="Destination, lieu ou pays")
    price = MoneySerializer(allow_null=True)
    price_unit = serializers.ChoiceField(choices=["person", "night", "day"], allow_null=True)
    score = serializers.FloatField()


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    count = serializers.IntegerField(help_text="Nombre total de résultats (tous types confondus)")
    counts = serializers.DictField(child=serializers.IntegerField(), help_text="Nombre de résultats par type")
    results = SearchResultSerializer(many=True)


def result_data(target, obj, request):
    """Résultat affichable, quel que soit le type de contenu."""
    if target.type == "vehicle":
        title, excerpt, context = f"{obj.brand} {obj.model}", obj.description, obj.get_category_display()
    elif target.type == "destination":
        title, excerpt, context = obj.name, obj.short_description, obj.country_code
    else:
        title = getattr(obj, target.title_field)
        excerpt = obj.short_description
        place = getattr(obj, target.destination_field, None) if target.destination_field else None
        context = place.name if place else getattr(obj, "location", "")
    image = obj.cover_image.url if obj.cover_image else None
    amount = getattr(obj, target.price_field) if target.price_field else None
    return {
        "type": target.type,
        "slug": obj.slug,
        "title": title,
        "excerpt": (excerpt or "")[:200],
        "image": request.build_absolute_uri(image) if image else None,
        "image_alt": obj.cover_alt or title,
        "context": context or "",
        "price": money_repr(amount, getattr(obj, "currency", None), request),
        "price_unit": target.price_unit if amount is not None else None,
        "score": round(obj.score, 3),
    }
