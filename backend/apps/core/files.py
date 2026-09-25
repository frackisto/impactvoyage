from pathlib import Path
from uuid import uuid4

from django.utils.deconstruct import deconstructible


@deconstructible
class UploadTo:
    """
    Renomme chaque fichier uploadé en UUID (pas de nom fourni par l'utilisateur,
    pas d'énumération) et le range dans le dossier UPLOAD_FOLDER du modèle,
    ou à défaut dans le dossier de son app.
    """

    def __call__(self, instance, filename):
        folder = getattr(instance, "UPLOAD_FOLDER", instance._meta.app_label)
        return f"{folder}/{uuid4().hex}{Path(filename).suffix.lower()}"

    def __eq__(self, other):
        return isinstance(other, UploadTo)
