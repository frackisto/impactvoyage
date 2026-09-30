from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from PIL import Image, ImageOps, UnidentifiedImageError

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 Mo (architecture § 8)
# Au-delà, une image compressée peut occuper des Go en mémoire une fois décodée
# (« bombe de décompression ») : 40 mégapixels couvrent tous les appareils photo courants.
MAX_IMAGE_PIXELS = 40_000_000
# Format réel (lu dans le contenu par Pillow) attendu pour chaque extension.
IMAGE_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_size):
        self.max_size = max_size

    def __call__(self, file):
        if file.size > self.max_size:
            raise ValidationError(
                "Fichier trop volumineux (%(size).1f Mo, maximum %(max).0f Mo).",
                code="file_too_large",
                params={"size": file.size / 1024 / 1024, "max": self.max_size / 1024 / 1024},
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_size == other.max_size


def validate_image_content(file):
    """
    Contrôle le contenu réel du fichier (Phase 23) : un format JPEG, PNG ou WebP qui
    correspond à son extension, et des dimensions raisonnables. L'extension seule ne
    prouve rien : un fichier d'un autre type renommé en .jpg est refusé.
    """
    extension = Path(file.name or "").suffix.lower().lstrip(".")
    if extension not in IMAGE_FORMATS:  # extension refusée par FileExtensionValidator
        return
    try:
        file.seek(0)
        with Image.open(file) as image:
            image_format = image.format
            width, height = image.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValidationError("Ce fichier n'est pas une image valide.",
                              code="invalid_image") from exc
    finally:
        file.seek(0)
    if IMAGE_FORMATS.get(extension) != image_format:
        raise ValidationError(
            "Le contenu du fichier (%(format)s) ne correspond pas à son extension (.%(ext)s).",
            code="image_format_mismatch", params={"format": image_format, "ext": extension},
        )
    if width * height > MAX_IMAGE_PIXELS:
        raise ValidationError(
            "Image trop grande (%(width)d × %(height)d pixels, maximum 40 mégapixels).",
            code="image_too_large", params={"width": width, "height": height},
        )


def strip_image_metadata(file):
    """
    Réencode une image envoyée par un visiteur (photo d'avis, avatar) sans ses
    métadonnées : les données EXIF d'une photo de téléphone contiennent souvent la
    position GPS et le modèle de l'appareil. L'orientation est appliquée aux pixels.
    """
    file.seek(0)
    with Image.open(file) as image:
        image_format = image.format
        cleaned = ImageOps.exif_transpose(image)
        if image_format == "JPEG" and cleaned.mode not in ("RGB", "L"):
            cleaned = cleaned.convert("RGB")
        output = BytesIO()
        options = {"quality": 90} if image_format in ("JPEG", "WEBP") else {"optimize": True}
        cleaned.save(output, format=image_format, **options)
    return ContentFile(output.getvalue(), name=Path(file.name).name)


# Le décodage est vérifié par Pillow (ImageField) ; on contrôle en plus l'extension,
# la taille, le format réel et les dimensions.
image_validators = [
    FileExtensionValidator(IMAGE_EXTENSIONS),
    MaxFileSizeValidator(MAX_IMAGE_SIZE),
    validate_image_content,
]
