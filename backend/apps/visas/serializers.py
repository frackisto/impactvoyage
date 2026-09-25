from rest_framework import serializers

from apps.core.serializers import LinesField, MoneyField

from .models import VisaService


class VisaServiceSerializer(serializers.ModelSerializer):
    fees = MoneyField(amount="fees")
    required_documents = LinesField()

    class Meta:
        model = VisaService
        fields = [
            "id", "destination_country_code", "country_slug", "nationality_code", "visa_type",
            "purpose", "validity_duration", "processing_time", "fees", "required_documents",
            "description",
        ]
