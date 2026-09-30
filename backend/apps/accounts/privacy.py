"""Données personnelles des comptes (apps/core/privacy.py)."""
from apps.core import privacy

from .models import User
from .otp import reset_devices
from .services import revoke_all_tokens


@privacy.register
class Accounts(privacy.PersonalDataSource):
    label = "Compte"

    def find(self, email):
        return User.objects.filter(email__iexact=email)

    def export(self, obj):
        return {
            "email": obj.email, "prenom": obj.first_name, "nom": obj.last_name,
            "telephone": obj.phone, "whatsapp": obj.whatsapp, "pays": obj.country_code,
            "avatar": obj.avatar.name if obj.avatar else "",
            "langue": obj.preferred_language, "devise": obj.preferred_currency,
            "role": obj.get_role_display(), "email_verifie": obj.is_verified,
            "inscription": obj.date_joined.isoformat(),
            "derniere_connexion": obj.last_login and obj.last_login.isoformat(),
        }

    def describe(self, obj):
        return f"{obj.email} ({obj.get_role_display()})"

    def decide(self, obj):
        if obj.is_staff:
            return privacy.KEEP, "compte de l'équipe : passez-le d'abord au rôle Client"
        return privacy.ANONYMIZE, ""

    def anonymize(self, obj):
        """Compte désactivé et vidé ; la ligne reste pour les réservations qui y sont liées."""
        revoke_all_tokens(obj)
        reset_devices(obj)
        if obj.avatar:
            obj.avatar.delete(save=False)
        obj.email = f"compte-supprime-{obj.pk}@anonyme.invalid"
        obj.first_name = obj.last_name = obj.phone = obj.whatsapp = obj.country_code = ""
        obj.is_active = obj.is_verified = False
        obj.set_unusable_password()
        obj.save()
