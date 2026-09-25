from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Utilisateur custom minimal pour permettre `migrate` dès la Phase 2 (initialisation).
    Les champs métier complets (téléphone, whatsapp, avatar...) seront
    ajoutés en Phase 3 « Création des modèles et migrations ».
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super administrateur"
        ADMIN = "ADMIN", "Administrateur"
        AGENT = "AGENT", "Agent"
        COMMERCIAL = "COMMERCIAL", "Commercial"
        GESTIONNAIRE = "GESTIONNAIRE", "Gestionnaire"
        CLIENT = "CLIENT", "Client"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CLIENT
    )

    def __str__(self):
        return self.get_full_name() or self.username
