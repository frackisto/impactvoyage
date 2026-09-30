from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.core.choices import Currency
from apps.core.files import UploadTo
from apps.core.validators import image_validators


class UserManager(BaseUserManager):
    """Gestionnaire d'utilisateurs identifiés par leur email."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Utilisateur de la plateforme, identifié par son email.
    Le rôle est la seule source de vérité : is_staff, is_superuser et le groupe
    de permissions en sont dérivés (accounts.roles, commande sync_roles).
    """

    UPLOAD_FOLDER = "avatars"

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super administrateur"
        ADMIN = "ADMIN", "Administrateur"
        AGENT = "AGENT", "Agent"
        COMMERCIAL = "COMMERCIAL", "Commercial"
        GESTIONNAIRE = "GESTIONNAIRE", "Gestionnaire"
        CLIENT = "CLIENT", "Client"

    username = None
    email = models.EmailField("adresse email", unique=True)
    role = models.CharField(
        "rôle", max_length=20, choices=Role.choices, default=Role.CLIENT, db_index=True
    )
    phone = models.CharField("téléphone", max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    country_code = models.CharField("pays (ISO 3166-1)", max_length=2, blank=True)
    avatar = models.ImageField(upload_to=UploadTo(), validators=image_validators, blank=True)
    preferred_language = models.CharField("langue préférée", max_length=5, default="fr")
    preferred_currency = models.CharField(
        "devise préférée", max_length=3, choices=Currency.choices, default=Currency.XOF
    )
    is_verified = models.BooleanField("email vérifié", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "utilisateur"
        ordering = ["email"]

    def __str__(self):
        return self.get_full_name() or self.email

    def save(self, *args, **kwargs):
        self.email = self.email.lower() if self.email else self.email
        self.is_superuser = self.role == self.Role.SUPER_ADMIN
        self.is_staff = self.role != self.Role.CLIENT
        super().save(*args, **kwargs)

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT
