from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
DEMO_DATA_ALLOWED = True

# Emails : Mailpit (service docker-compose) les capture tous, rien ne part vraiment.
# Interface : http://localhost:8025. Un EMAIL_HOST défini dans .env reste prioritaire.
if not env("EMAIL_HOST", default=""):  # noqa: F405
    EMAIL_HOST = "mailpit"
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False

# En dev, affichage complet des erreurs, pas de sécurité renforcée.
INSTALLED_APPS += []  # noqa: F405
