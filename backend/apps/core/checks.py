"""
Vérifications au démarrage (manage.py check, runserver, migrate...).

Piège réel rencontré : dans un fichier .env, une valeur non entourée de
guillemets est coupée au premier « # » par django-environ. Une SECRET_KEY
générée par Django en contient souvent : elle se retrouve silencieusement
réduite à quelques caractères.
"""
from django.conf import settings
from django.core.checks import Warning, register

MIN_KEY_LENGTH = 32


@register()
def secret_keys_length(app_configs, **kwargs):
    issues = []
    keys = {
        "SECRET_KEY": settings.SECRET_KEY,
        "SIMPLE_JWT['SIGNING_KEY']": settings.SIMPLE_JWT.get("SIGNING_KEY", ""),
    }
    for name, value in keys.items():
        if len(value or "") < MIN_KEY_LENGTH:
            issues.append(Warning(
                f"{name} ne fait que {len(value or '')} caractères (minimum {MIN_KEY_LENGTH}).",
                hint="Dans .env, entourez la valeur de guillemets si elle contient « # » ou "
                     "« $ » : elle est sinon tronquée au premier « # ».",
                id="core.W001",
            ))
    return issues


@register(deploy=True)
def security_settings(app_configs, **kwargs):
    """Réglages de sécurité de la Phase 23, vérifiés par « manage.py check --deploy »."""
    issues = []
    if not settings.TURNSTILE_SECRET_KEY:
        issues.append(Warning(
            "TURNSTILE_SECRET_KEY est vide : les formulaires publics ne sont protégés que "
            "par le champ piège et la limitation de débit.",
            hint="Créez un widget Turnstile (tableau de bord Cloudflare) et renseignez la clé "
                 "secrète (backend) et la clé du site (NEXT_PUBLIC_TURNSTILE_SITE_KEY).",
            id="core.W002",
        ))
    if settings.ADMIN_URL == "admin/":
        issues.append(Warning(
            "Le backoffice est à l'adresse standard /admin/, la première essayée par les robots.",
            hint="Définissez ADMIN_URL_PATH (ex. « gestion-7k2p »).",
            id="core.W003",
        ))
    if not settings.STAFF_OTP_REQUIRED:
        issues.append(Warning(
            "La double authentification de l'équipe est désactivée (STAFF_OTP_REQUIRED).",
            id="core.W004",
        ))
    return issues
