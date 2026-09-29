from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import ROLE_RESOURCES, group_name, permissions_for_role
from apps.core.tests.helpers import make_departure, make_user
from apps.core.tests.test_api import API, ApiTestCase


class RoleMatrixTests(TestCase):
    def test_every_permission_of_the_matrix_exists(self):
        """Une faute de frappe dans accounts.roles ferait disparaître un droit en silence."""
        from django.contrib.auth.models import Permission

        existing = {f"{p.content_type.app_label}.{p.codename}"
                    for p in Permission.objects.select_related("content_type")}
        for role in ROLE_RESOURCES:
            with self.subTest(role=role):
                self.assertLessEqual(permissions_for_role(role), existing)

    def test_groups_are_created_by_migrate_and_follow_the_role(self):
        self.assertEqual(Group.objects.filter(name__startswith="Rôle").count(), len(User.Role))
        user = make_user("AGENT")
        self.assertEqual([g.name for g in user.groups.all()], [group_name("AGENT")])
        self.assertTrue(user.has_perm("tours.change_tour"))
        self.assertFalse(user.has_perm("bookings.change_booking"))

        user.role = User.Role.COMMERCIAL
        user.save()
        user = User.objects.get(pk=user.pk)  # cache de permissions réinitialisé
        self.assertEqual([g.name for g in user.groups.all()], [group_name("COMMERCIAL")])
        self.assertTrue(user.has_perm("bookings.change_booking"))
        self.assertFalse(user.has_perm("tours.change_tour"))

    def test_super_admin_is_derived_from_the_role(self):
        user = make_user("SUPER_ADMIN")
        self.assertTrue(user.is_superuser and user.has_perm("payments.delete_payment"))
        user.role = User.Role.ADMIN
        user.save()
        user = User.objects.get(pk=user.pk)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_perm("core.change_sitesettings"))
        self.assertTrue(user.has_perm("accounts.change_user"))

    def test_client_has_no_permission(self):
        self.assertEqual(make_user("CLIENT").get_all_permissions(), set())

    def test_sync_roles_command_is_idempotent(self):
        make_user("GESTIONNAIRE")
        out = StringIO()
        call_command("sync_roles", stdout=out)
        call_command("sync_roles", stdout=out)
        self.assertEqual(Group.objects.filter(name__startswith="Rôle").count(), len(User.Role))
        self.assertIn("utilisateur(s) rangé(s)", out.getvalue())


class RolePermissionApiTests(ApiTestCase):
    """Les droits de l'API suivent la matrice des rôles."""

    def setUp(self):
        super().setUp()
        departure = make_departure(start_date=timezone.localdate() + timedelta(days=30),
                                   end_date=timezone.localdate() + timedelta(days=32))
        self.reference = self.client.post(f"{API}/bookings/", {
            "contact_name": "Awa", "contact_email": "awa@example.com",
            "contact_phone": "+2250700000000", "consent": True,
            "items": [{"kind": "tour_departure", "object_id": departure.pk, "quantity": 1}],
        }, format="json").data["reference"]

    def as_role(self, role):
        self.client.force_authenticate(make_user(role))

    def test_booking_rights_by_role(self):
        self.as_role("AGENT")  # contenu uniquement : ne voit que ses propres réservations
        self.assertEqual(self.client.get(f"{API}/bookings/").data["count"], 0)
        self.assertEqual(self.client.post(f"{API}/bookings/{self.reference}/confirm/")
                         .status_code, 403)

        self.as_role("GESTIONNAIRE")  # voit tout, ne décide pas, n'annule pas pour autrui
        self.assertEqual(self.client.get(f"{API}/bookings/").data["count"], 1)
        self.assertEqual(self.client.post(f"{API}/bookings/{self.reference}/confirm/")
                         .status_code, 403)
        self.assertEqual(self.client.post(f"{API}/bookings/{self.reference}/cancel/")
                         .status_code, 403)

        self.as_role("COMMERCIAL")
        self.assertEqual(self.client.post(f"{API}/bookings/{self.reference}/confirm/")
                         .status_code, 200)

    def test_quote_rights_by_role(self):
        self.as_role("GESTIONNAIRE")
        self.assertEqual(self.client.get(f"{API}/quotes/").status_code, 403)
        self.as_role("COMMERCIAL")
        self.assertEqual(self.client.get(f"{API}/quotes/").status_code, 200)
