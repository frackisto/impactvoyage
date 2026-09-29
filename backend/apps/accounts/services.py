"""
Comptes : inscription, vérification de l'email, mots de passe, révocation des
jetons (CdC § 24 ; architecture § 6.1).
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.core.exceptions import BusinessError
from apps.notifications.emails import send_email

from . import emails

User = get_user_model()

VERIFY_EMAIL_SALT = "accounts.verify-email"


# --- Inscription et vérification de l'email ---------------------------------


@transaction.atomic
def register_user(*, email, password, **profile):
    """Crée un compte client et envoie le lien de vérification de l'email."""
    user = User.objects.create_user(email, password, role=User.Role.CLIENT, **profile)
    send_verification_email(user)
    return user


def make_email_verification_token(user):
    # L'email fait partie du jeton : le changer invalide les liens déjà envoyés.
    return signing.dumps({"uid": user.pk, "email": user.email}, salt=VERIFY_EMAIL_SALT)


def send_verification_email(user):
    if user.is_verified:
        raise BusinessError("Cette adresse email est déjà vérifiée.", code="already_verified")
    send_email(user.email, emails.verification(user, make_email_verification_token(user)))


def verify_email(token):
    invalid = BusinessError("Lien de vérification invalide ou expiré.", code="invalid_token")
    try:
        data = signing.loads(
            token, salt=VERIFY_EMAIL_SALT, max_age=settings.EMAIL_VERIFICATION_MAX_AGE
        )
    except signing.BadSignature:  # inclut SignatureExpired
        raise invalid from None
    user = User.objects.filter(pk=data.get("uid"), email=data.get("email"), is_active=True).first()
    if user is None:
        raise invalid
    if not user.is_verified:
        user.is_verified = True
        user.save(update_fields=["is_verified"])
    return user


# --- Mots de passe et jetons -------------------------------------------------


def revoke_all_tokens(user):
    """Déconnecte l'utilisateur partout : tous ses refresh tokens sont révoqués."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


@transaction.atomic
def change_password(user, new_password):
    user.set_password(new_password)
    user.save(update_fields=["password"])
    revoke_all_tokens(user)
    return user


def request_password_reset(email):
    """
    Envoie un lien de réinitialisation si un compte actif existe. Ne dit jamais
    si l'email est connu (pas d'énumération des comptes).
    """
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    minutes = settings.PASSWORD_RESET_TIMEOUT // 60
    send_email(user.email, emails.password_reset(user, uid, token, minutes))


@transaction.atomic
def reset_password(uid, token, new_password):
    """Le jeton Django devient invalide dès que le mot de passe change (usage unique)."""
    invalid = BusinessError("Lien de réinitialisation invalide ou expiré.", code="invalid_token")
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
    except (ValueError, TypeError, OverflowError, User.DoesNotExist):
        raise invalid from None
    if not default_token_generator.check_token(user, token):
        raise invalid
    validate_password(new_password, user=user)
    return change_password(user, new_password)
