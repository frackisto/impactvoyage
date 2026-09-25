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
