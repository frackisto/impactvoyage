from .base import *  # noqa: F401,F403

DEBUG = False

# Aucune valeur par défaut en production : l'application refuse de démarrer
# si la clé n'est pas fournie.
SECRET_KEY = env("SECRET_KEY")  # noqa: F405

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
