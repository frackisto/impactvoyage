from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES["default"]["NAME"] = "test_voyage_db"  # noqa: F405

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # rapide pour les tests
]

# Tests indépendants de Redis (cache et compteurs du rate limiting).
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
