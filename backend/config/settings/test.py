from .base import *  # noqa: F401,F403

DEBUG = False

# Clés propres aux tests : indépendantes du .env local.
SECRET_KEY = "tests-" + "x" * 60
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": "tests-jwt-" + "y" * 40}  # noqa: F405

DATABASES["default"]["NAME"] = "test_voyage_db"  # noqa: F405

DEMO_DATA_ALLOWED = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # rapide pour les tests
]

# Fichiers uploadés gardés en mémoire pendant les tests (rien n'est écrit sur disque).
STORAGES = {
    **STORAGES,  # noqa: F405
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
}

# Tests indépendants de Redis (cache et compteurs du rate limiting).
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
