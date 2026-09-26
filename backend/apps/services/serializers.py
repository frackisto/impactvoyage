from rest_framework import serializers

from apps.core.serializers import MoneyField

from .models import Service, ServicePrice


class ServicePriceSerializer(serializers.ModelSerializer):
    price = MoneyField(amount="price")

    class Meta:
        model = ServicePrice
        fields = ["id", "label", "price", "unit"]


class ServiceSerializer(serializers.ModelSerializer):
    prices = ServicePriceSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            "id", "slug", "title", "short_description", "description", "icon",
            "quote_service_type", "prices",
        ]
