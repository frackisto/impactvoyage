from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


@transaction.atomic
def register_user(*, email, password, **profile):
    """Crée un compte client. La vérification de l'email est ajoutée en Phase 7."""
    return User.objects.create_user(email, password, role=User.Role.CLIENT, **profile)


def change_password(user, new_password):
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
