from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 Mo (architecture § 8)


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


# Le contenu réel est vérifié par Pillow (ImageField) ; on contrôle en plus
# l'extension et la taille.
image_validators = [
    FileExtensionValidator(IMAGE_EXTENSIONS),
    MaxFileSizeValidator(MAX_IMAGE_SIZE),
]
