from rest_framework import serializers

from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id", "slug", "title", "short_description", "description", "icon",
            "quote_service_type",
        ]
