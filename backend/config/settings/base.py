"""
Settings de base — communs à dev, prod et test.
"""
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import environ
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="unsafe-secret-key-for-dev-only")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# --- Applications ---
DJANGO_APPS = [
    # modeltranslation doit précéder l'admin pour patcher ses formulaires.
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.destinations",
    "apps.tours",
    "apps.accommodations",
    "apps.vehicles",
    "apps.activities",
    "apps.events",
    "apps.media",
    "apps.bookings",
    "apps.services",
    "apps.visas",
    "apps.transport",
    "apps.inquiries",
    "apps.notifications",
    "apps.reviews",
    "apps.offers",
    "apps.blog",
    "apps.payments",
    "apps.search",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "apps.core.middleware.QueryLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de données ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="127.0.0.1"),
        "PORT": env("DATABASE_PORT", default="5432"),
    }
}

# --- Utilisateur custom ---
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation ---
LANGUAGE_CODE = "fr"
# Langues initiales (cahier des charges § 36). Espagnol, portugais et arabe
# seront ajoutés ici plus tard ; l'arabe impose un rendu RTL côté frontend.
LANGUAGES = [
    ("fr", "Français"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# Contenus traduits (django-modeltranslation) : une colonne par langue.
# Si la traduction anglaise est vide, on affiche le français.
MODELTRANSLATION_DEFAULT_LANGUAGE = "fr"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("fr",)
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Devises ---
# Prix stockés en FCFA (XOF) ; les autres devises ne servent qu'à l'affichage.
DEFAULT_CURRENCY = "XOF"
DISPLAY_CURRENCIES = ["XOF", "EUR", "USD", "GBP"]
# Parité fixe du franc CFA (UEMOA) : 1 EUR = 655,957 XOF.
XOF_PER_EUR = Decimal("655.957")
EXCHANGE_RATES_API_URL = env(
    "EXCHANGE_RATES_API_URL", default="https://api.frankfurter.dev/v1/latest"
)

# --- Réservations (architecture § 3.8) ---
BOOKING_HOLD_MINUTES = 30  # réservation directe en attente de paiement
QUOTE_BOOKING_HOLD_HOURS = 48  # réservation issue d'un devis accepté

# Données fictives (python manage.py seed_demo) : autorisées en dev et en tests seulement.
DEMO_DATA_ALLOWED = False

# --- Fichiers statiques / médias ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# « default » est obligatoire dès que STORAGES est défini : sans lui, aucun upload
# (photos, avatars) ne fonctionne.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 12,
    # Format d'erreur unique : {"error": {"code", "message", "details"}} (architecture § 5.1).
    "EXCEPTION_HANDLER": "apps.core.api.api_exception_handler",
    # Rate limiting (cahier § 29). Les scopes "auth", "quotes", "contact" et
    # "reviews" sont appliqués aux vues concernées via ScopedRateThrottle.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "300/min",
        "auth": "10/min",
        "quotes": "5/hour",
        "bookings": "10/hour",
        "contact": "5/hour",
        "reviews": "3/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API Agence de Voyage",
    "DESCRIPTION": "Documentation de l'API REST de la plateforme de l'agence de voyage.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Schémas distincts lecture / écriture (ex. upload de photo d'avis).
    "COMPONENT_SPLIT_REQUEST": True,
    # Noms explicites des enums partagés ou homonymes (types TypeScript lisibles, Phase 8).
    "ENUM_NAME_OVERRIDES": {
        "CurrencyEnum": "apps.core.choices.Currency",
        "DisplayCurrencyEnum": ["EUR", "USD", "GBP"],
        "RequestedServiceEnum": "apps.core.choices.RequestedService",
        "BookingStatusEnum": "apps.bookings.models.Booking.Status",
        "QuoteStatusEnum": "apps.inquiries.models.QuoteRequest.Status",
        "DepartureStatusEnum": "apps.tours.models.TourDeparture.Status",
        "VehicleCategoryEnum": "apps.vehicles.models.Vehicle.Category",
        "EventCategoryEnum": "apps.events.models.Event.Category",
    },
}

# --- JWT ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("ACCESS_TOKEN_LIFETIME_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Clé de signature distincte de SECRET_KEY (cahier § 29 : JWT_SECRET) :
    # la faire tourner invalide les jetons sans toucher aux sessions ni aux
    # liens de réinitialisation de mot de passe.
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "UPDATE_LAST_LOGIN": True,
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.LoginSerializer",
}

# Liens envoyés par email (architecture § 6.1).
PASSWORD_RESET_TIMEOUT = 2 * 60 * 60  # 2 heures, usage unique
EMAIL_VERIFICATION_MAX_AGE = 3 * 24 * 60 * 60  # 3 jours

# --- CORS ---
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True

# --- Cache Redis ---
# Base Redis dédiée (2 par défaut) : un cache.clear() ne doit jamais vider
# la file de tâches Celery, qui vit dans la base 0.
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env(
            "REDIS_CACHE_URL", default=REDIS_URL.rsplit("/", 1)[0] + "/2"
        ),
        "KEY_PREFIX": "voyage",
        "TIMEOUT": 300,
    }
}

# --- Celery / Redis ---
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "expire-pending-bookings": {
        "task": "apps.bookings.tasks.expire_pending_bookings_task",
        "schedule": crontab(minute="*/5"),
    },
    "complete-past-bookings": {
        "task": "apps.bookings.tasks.complete_past_bookings_task",
        "schedule": crontab(hour=2, minute=0),
    },
    "update-exchange-rates": {
        "task": "apps.core.tasks.update_exchange_rates_task",
        # Après la publication des taux de la BCE (~16 h, heure d'Europe centrale).
        "schedule": crontab(hour=16, minute=30),
    },
}

# --- Email ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@agence-voyage.com")
AGENCY_NOTIFICATION_EMAIL = env("AGENCY_NOTIFICATION_EMAIL", default="contact@agence-voyage.com")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
BACKEND_URL = env("BACKEND_URL", default="http://localhost:8000")
