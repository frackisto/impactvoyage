from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(OpenApiTypes.STR)
class CommaSeparatedIntegerField(serializers.Field):
    """?amenities=1,4,7 → [1, 4, 7]."""

    def to_internal_value(self, data):
        try:
            return [int(x) for x in str(data).split(",") if x.strip()]
        except ValueError as exc:
            raise serializers.ValidationError("Liste d'identifiants attendue (ex. 1,4,7).") from exc

    def to_representation(self, value):
        return ",".join(str(v) for v in value)


class PriceRangeParams(serializers.Serializer):
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0,
                                         required=False)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0,
                                         required=False)

    def validate(self, attrs):
        low, high = attrs.get("min_price"), attrs.get("max_price")
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError({"max_price": "Le budget maximum est inférieur au minimum."})
        return attrs


class PeriodParams(serializers.Serializer):
    """Période optionnelle : les deux bornes ou aucune."""

    start_field, end_field = "available_from", "available_to"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start, end = attrs.get(self.start_field), attrs.get(self.end_field)
        if bool(start) != bool(end):
            raise serializers.ValidationError("Indiquez une date de début et une date de fin.")
        if start and end <= start:
            raise serializers.ValidationError({self.end_field: "La fin doit suivre le début."})
        return attrs
