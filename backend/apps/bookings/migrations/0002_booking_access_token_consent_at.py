import uuid

from django.db import migrations, models


def fill_tokens(apps, schema_editor):
    """Un jeton distinct par réservation existante (un default unique serait partagé)."""
    Booking = apps.get_model("bookings", "Booking")
    for booking in Booking._base_manager.filter(access_token__isnull=True).only("pk"):
        booking.access_token = uuid.uuid4()
        booking.save(update_fields=["access_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="access_token",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(fill_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="booking",
            name="access_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="consent_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="consentement au traitement des données"
            ),
        ),
    ]
