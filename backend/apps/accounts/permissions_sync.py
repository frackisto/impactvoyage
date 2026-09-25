"""Synchronisation des groupes Django avec la matrice des rôles (accounts.roles)."""
import logging

from django.contrib.auth.models import Group, Permission

from .models import User
from .roles import group_name, permissions_for_role

logger = logging.getLogger(__name__)


def sync_role_groups():
    """Crée ou met à jour un groupe par rôle ; idempotent. Retourne {rôle: nb de permissions}."""
    existing = {
        f"{p.content_type.app_label}.{p.codename}": p
        for p in Permission.objects.select_related("content_type")
    }
    summary = {}
    for role in User.Role.values:
        wanted = permissions_for_role(role)
        missing = wanted - existing.keys()
        if missing:
            logger.warning("Permissions introuvables pour %s : %s", role, sorted(missing))
        group, _ = Group.objects.get_or_create(name=group_name(role))
        group.permissions.set([existing[p] for p in wanted if p in existing])
        summary[role] = len(wanted) - len(missing)
    return summary


def assign_role_group(user):
    """Place l'utilisateur dans le seul groupe de son rôle."""
    groups = list(Group.objects.filter(name__in=[group_name(r) for r in User.Role.values]))
    role_group = next((g for g in groups if g.name == group_name(user.role)), None)
    if role_group is None:
        role_group, _ = Group.objects.get_or_create(name=group_name(user.role))
    user.groups.remove(*[g for g in groups if g != role_group])
    user.groups.add(role_group)
