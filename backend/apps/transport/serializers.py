from rest_framework import serializers

from apps.core.serializers import MoneyField

from .models import TransportService


class TransportServiceSerializer(serializers.ModelSerializer):
    price_from = MoneyField(amount="price_from")

    class Meta:
        model = TransportService
        fields = [
            "id", "slug", "title", "description", "transport_type", "origin", "destination",
            "max_passengers", "price_from", "schedule_info", "cover_image", "cover_alt",
        ]
