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

# Double authentification de l'équipe : facultative en développement (comptes de
# démonstration) ; STAFF_OTP_REQUIRED=True dans .env pour l'essayer. Toujours active en production.
STAFF_OTP_REQUIRED = env.bool("STAFF_OTP_REQUIRED", default=False)  # noqa: F405
API_DOCS_PUBLIC = env.bool("API_DOCS_PUBLIC", default=True)  # noqa: F405
