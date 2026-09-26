from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
DEMO_DATA_ALLOWED = True

# En dev, affichage complet des erreurs, pas de sécurité renforcée.
INSTALLED_APPS += []  # noqa: F405
