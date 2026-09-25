"""
Référence courte d'une destination, imbriquée dans les circuits, hôtels,
activités... Module séparé : destinations.serializers importe ces apps.
"""
from rest_framework import serializers

from .models import Destination


class DestinationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["id", "slug", "name", "continent", "country_code", "city"]
