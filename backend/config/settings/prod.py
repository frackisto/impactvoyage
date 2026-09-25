from .base import *  # noqa: F401,F403

DEBUG = False

from django.core.exceptions import ImproperlyConfigured  # noqa: E402

# Aucune valeur par défaut en production : l'application refuse de démarrer
# si une clé manque ou est trop courte (ex. tronquée au premier « # » d'un .env).
SECRET_KEY = env("SECRET_KEY")  # noqa: F405
SIMPLE_JWT["SIGNING_KEY"] = env("JWT_SIGNING_KEY")  # noqa: F405
for _name, _value, _min in (("SECRET_KEY", SECRET_KEY, 50),
                            ("JWT_SIGNING_KEY", SIMPLE_JWT["SIGNING_KEY"], 32)):  # noqa: F405
    if len(_value) < _min:
        raise ImproperlyConfigured(f"{_name} doit faire au moins {_min} caractères.")

# Derrière Nginx, qui termine le TLS : sans cet en-tête, Django verrait
# toutes les requêtes en HTTP et SECURE_SSL_REDIRECT bouclerait à l'infini.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
