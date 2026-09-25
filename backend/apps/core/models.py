from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .choices import Currency
from .files import UploadTo
from .validators import image_validators


class TimeStampedModel(models.Model):
    """Ajoute les champs created_at / updated_at à tout modèle héritier."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SlugMixin(models.Model):
    """Ajoute un champ slug unique, utilisé pour les URLs SEO-friendly."""

    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class SoftDeleteModel(models.Model):
    """
    Suppression logique : deleted_at renseigné au lieu d'une suppression réelle.
    Utile pour Booking, QuoteRequest, etc.
    """

    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class PublishableQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class PublishableMixin(models.Model):
    """Contenu public masquable sans suppression (brouillon, hors saison...)."""

    is_published = models.BooleanField("publié", default=True, db_index=True)

    objects = PublishableQuerySet.as_manager()

    class Meta:
        abstract = True


class CoverImageMixin(models.Model):
    """
    Image principale d'un contenu public. Le dossier d'upload est donné par
    l'attribut de classe UPLOAD_FOLDER du modèle concret.
    """

    cover_image = models.ImageField(
        "image principale", upload_to=UploadTo(), validators=image_validators, blank=True
    )
    cover_alt = models.CharField("texte alternatif", max_length=255, blank=True)

    class Meta:
        abstract = True


class GalleryImage(models.Model):
    """Base des galeries photo (DestinationImage, TourImage, HotelImage...)."""

    image = models.ImageField(
        upload_to=UploadTo(),
        validators=image_validators,
        width_field="width",
        height_field="height",
    )
    width = models.PositiveIntegerField(null=True, editable=False)
    height = models.PositiveIntegerField(null=True, editable=False)
    alt_text = models.CharField("texte alternatif", max_length=255)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        abstract = True
        ordering = ["order", "id"]

    def __str__(self):
        return self.alt_text


class MediaAsset(models.Model):
    """Photo (fichier) ou vidéo (lien YouTube/Vimeo) d'une galerie mixte."""

    class Type(models.TextChoices):
        PHOTO = "PHOTO", "Photo"
        VIDEO = "VIDEO", "Vidéo"

    type = models.CharField(max_length=5, choices=Type.choices, default=Type.PHOTO)
    image = models.ImageField(
        upload_to=UploadTo(),
        validators=image_validators,
        width_field="width",
        height_field="height",
        blank=True,
    )
    width = models.PositiveIntegerField(null=True, editable=False)
    height = models.PositiveIntegerField(null=True, editable=False)
    video_url = models.URLField("lien vidéo", blank=True)
    alt_text = models.CharField("texte alternatif", max_length=255, blank=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        abstract = True
        ordering = ["order", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(type="PHOTO") & ~models.Q(image="")
                    | models.Q(type="VIDEO") & ~models.Q(video_url="")
                ),
                name="%(app_label)s_%(class)s_photo_or_video",
            ),
        ]


class BookableMixin(models.Model):
    """Offre réservable : Tour, Room, Residence, Vehicle, Activity."""

    class BookingMode(models.TextChoices):
        INSTANT = "INSTANT", "Réservation directe"
        ON_REQUEST = "ON_REQUEST", "Sur demande"

    booking_mode = models.CharField(
        "mode de réservation",
        max_length=10,
        choices=BookingMode.choices,
        default=BookingMode.ON_REQUEST,
    )
    base_price = models.DecimalField(
        "prix de base", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(
        "devise", max_length=3, choices=Currency.choices, default=Currency.XOF
    )

    class Meta:
        abstract = True


class ReferenceMixin(models.Model):
    """
    Référence lisible et séquentielle (ex. IV-2026-000123), attribuée après
    le premier enregistrement à partir de la clé primaire. Définir
    REFERENCE_PREFIX sur le modèle concret.
    """

    REFERENCE_PREFIX = "REF"

    reference = models.CharField(
        "référence", max_length=20, unique=True, null=True, editable=False
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        creating = self.reference is None
        super().save(*args, **kwargs)
        if creating:
            self.reference = (
                f"{self.REFERENCE_PREFIX}-{timezone.now():%Y}-{self.pk:06d}"
            )
            type(self)._base_manager.filter(pk=self.pk).update(reference=self.reference)


class Category(TimeStampedModel):
    """Catégories partagées : thèmes de circuits, activités, blog, événements, médias."""

    class Kind(models.TextChoices):
        TOUR_THEME = "TOUR_THEME", "Thème de circuit"
        ACTIVITY = "ACTIVITY", "Activité"
        BLOG = "BLOG", "Blog"
        MEDIA = "MEDIA", "Médiathèque"

    name = models.CharField("nom", max_length=100)
    slug = models.SlugField(max_length=120)
    kind = models.CharField("type", max_length=20, choices=Kind.choices, db_index=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        verbose_name = "catégorie"
        ordering = ["kind", "order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["kind", "slug"], name="unique_category_slug_per_kind"),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.name}"


class Tag(models.Model):
    name = models.CharField("nom", max_length=60)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SiteSettings(TimeStampedModel):
    """
    Informations de l'agence éditables dans l'admin (singleton, pk=1) :
    coordonnées, réseaux sociaux, hero de l'accueil, page « À propos ».
    """

    UPLOAD_FOLDER = "site"

    agency_name = models.CharField("nom de l'agence", max_length=150, default="Impact Voyage")
    slogan = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.CharField("sous-titre du hero", max_length=300, blank=True)
    hero_image = models.ImageField(
        "image du hero", upload_to=UploadTo(), validators=image_validators, blank=True
    )
    hero_video_url = models.URLField("vidéo du hero", blank=True)
    phone = models.CharField("téléphone", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    address = models.CharField("adresse", max_length=255, blank=True)
    opening_hours = models.TextField("horaires", blank=True)
    social_links = models.JSONField(
        "réseaux sociaux",
        default=dict,
        blank=True,
        help_text='Ex. {"facebook": "https://…", "instagram": "https://…"}',
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    about_content = models.TextField("contenu « À propos »", blank=True)

    class Meta:
        verbose_name = "paramètres du site"
        verbose_name_plural = "paramètres du site"

    def __str__(self):
        return self.agency_name

    def save(self, *args, **kwargs):
        self.pk = 1
        if self._state.adding:
            # Nouvelle instance alors que la ligne existe : Django fera un
            # UPDATE, il faut conserver la date de création d'origine.
            existing = type(self).objects.filter(pk=1).values_list("created_at", flat=True)
            self.created_at = existing.first() or self.created_at
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ExchangeRate(models.Model):
    """Taux d'affichage : 1 XOF = rate_from_xof unités de la devise."""

    currency = models.CharField(
        "devise",
        max_length=3,
        unique=True,
        choices=[c for c in Currency.choices if c[0] != settings.DEFAULT_CURRENCY],
    )
    rate_from_xof = models.DecimalField(
        "taux depuis XOF",
        max_digits=18,
        decimal_places=10,
        validators=[MinValueValidator(0), MaxValueValidator(1_000_000)],
    )
    fetched_at = models.DateTimeField("mis à jour le", default=timezone.now)

    class Meta:
        verbose_name = "taux de change"
        verbose_name_plural = "taux de change"
        ordering = ["currency"]

    def __str__(self):
        return f"1 XOF = {self.rate_from_xof} {self.currency}"
