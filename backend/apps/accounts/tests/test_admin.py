from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.accounts.models import User
from apps.core.tests.admin_helpers import AdminTestCase, change_form_data
from apps.core.tests.helpers import make_user


class UserAdminTests(AdminTestCase):
    def test_groups_are_not_editable_by_hand(self):
        self.assertNotIn(Group, admin.site._registry)

    def test_admin_creates_a_staff_account_with_a_role(self):
        self.login("ADMIN")
        response = self.client.post(reverse("admin:accounts_user_add"), {
            "email": "Nouvel.Agent@Example.com", "role": "AGENT",
            "password1": "Un-mot-de-passe-solide-2026", "password2": "Un-mot-de-passe-solide-2026",
            "usable_password": "true",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="nouvel.agent@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.has_perm("tours.change_tour"))

    def test_admin_cannot_grant_the_super_admin_role(self):
        self.login("ADMIN")
        response = self.client.post(reverse("admin:accounts_user_add"), {
            "email": "pirate@example.com", "role": "SUPER_ADMIN",
            "password1": "Un-mot-de-passe-solide-2026", "password2": "Un-mot-de-passe-solide-2026",
            "usable_password": "true",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("role", response.context["adminform"].form.errors)
        self.assertFalse(User.objects.filter(email="pirate@example.com").exists())

        colleague = make_user("AGENT")
        url = reverse("admin:accounts_user_change", args=[colleague.pk])
        self.client.post(url, change_form_data(self.client.get(url), role="SUPER_ADMIN", _save=""))
        colleague.refresh_from_db()
        self.assertEqual(colleague.role, "AGENT")

    def test_admin_cannot_modify_a_super_admin_account(self):
        self.login("ADMIN")
        boss = make_user("SUPER_ADMIN")
        response = self.client.get(reverse("admin:accounts_user_change", args=[boss.pk]))
        self.assertFalse(response.context["has_change_permission"])
        password_url = reverse("admin:auth_user_password_change", args=[boss.pk])
        self.assertEqual(self.client.get(password_url).status_code, 403)

    def test_super_admin_can_promote(self):
        self.login("SUPER_ADMIN")
        colleague = make_user("ADMIN")
        url = reverse("admin:accounts_user_change", args=[colleague.pk])
        self.client.post(url, change_form_data(self.client.get(url), role="SUPER_ADMIN", _save=""))
        colleague.refresh_from_db()
        self.assertTrue(colleague.is_superuser)
