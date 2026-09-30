"""
Double authentification de l'équipe (Phase 23, architecture § 11).

Chaque membre de l'équipe enregistre une application d'authentification (TOTP :
Google Authenticator, Microsoft Authenticator, FreeOTP…) et reçoit des codes de
secours à usage unique. Le code est demandé après le mot de passe, dans le
backoffice (apps/accounts/middleware.py) comme à la connexion à l'API
(LoginSerializer). django-otp limite les essais : chaque échec double le délai
avant le suivant.
"""
from django.conf import settings
from django.db import transaction
from django_otp import devices_for_user, user_has_device
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.core.exceptions import BusinessError


class TwoFactorError(BusinessError):
    """Connexion à l'API d'un membre de l'équipe sans code valide (voir LoginSerializer)."""

    code = "otp_required"
    status_code = 401


TOTP_DEVICE_NAME = "Application d'authentification"
BACKUP_DEVICE_NAME = "Codes de secours"


def otp_required(user):
    """Vrai si ce compte doit fournir un code : membre de l'équipe, 2FA activée."""
    return bool(settings.STAFF_OTP_REQUIRED and user.is_authenticated and user.is_staff)


def has_confirmed_device(user):
    return user_has_device(user, confirmed=True)


def pending_totp_device(user):
    """Appareil TOTP en cours d'enregistrement (clé secrète affichée en QR code)."""
    device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
    return device or TOTPDevice.objects.create(user=user, name=TOTP_DEVICE_NAME, confirmed=False)


def normalize(token):
    return "".join((token or "").split()).lower()


@transaction.atomic
def confirm_totp_device(device, token):
    """
    Valide l'enregistrement avec un premier code ; renvoie les codes de secours
    (affichés une seule fois) ou None si le code est faux.
    """
    device = TOTPDevice.objects.select_for_update().get(pk=device.pk)
    if not device.verify_token(normalize(token)):
        return None
    device.confirmed = True
    device.save(update_fields=["confirmed"])
    # Une seule application active : les anciens enregistrements sont retirés.
    TOTPDevice.objects.filter(user=device.user).exclude(pk=device.pk).delete()
    return regenerate_backup_codes(device.user)


def regenerate_backup_codes(user):
    StaticDevice.objects.filter(user=user).delete()
    backup = StaticDevice.objects.create(user=user, name=BACKUP_DEVICE_NAME, confirmed=True)
    codes = [StaticToken.random_token() for _ in range(settings.STAFF_OTP_BACKUP_CODES)]
    StaticToken.objects.bulk_create(StaticToken(device=backup, token=code) for code in codes)
    return codes


def verify_code(user, token):
    """
    Vérifie un code (application ou code de secours, consommé) ; renvoie l'appareil
    qui l'a accepté, sinon None. Les échecs augmentent le délai imposé par django-otp.
    """
    token = normalize(token)
    if not token:
        return None
    # 6 chiffres : application ; sinon code de secours (8 caractères). Un code n'est
    # soumis qu'au bon type d'appareil, pour ne pas compter un échec à l'autre.
    model = TOTPDevice if token.isdigit() and len(token) == 6 else StaticDevice
    with transaction.atomic():
        for device in devices_for_user(user, confirmed=True, for_verify=True):
            if isinstance(device, model) and device.verify_token(token):
                return device
    return None


def reset_devices(user):
    """Retire l'application et les codes de secours (téléphone perdu) : nouvel enregistrement."""
    for model in (TOTPDevice, StaticDevice):
        model.objects.filter(user=user).delete()
