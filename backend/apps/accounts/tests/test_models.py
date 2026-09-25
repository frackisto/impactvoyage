from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_email_is_the_login_and_is_lowercased(self):
        user = User.objects.create_user("Awa.Kone@Example.com", "mot-de-passe-solide")
        self.assertEqual(user.email, "awa.kone@example.com")
        self.assertEqual(
            authenticate(email="awa.kone@example.com", password="mot-de-passe-solide"), user
        )

    def test_client_is_not_staff(self):
        user = User.objects.create_user("client@example.com", "x")
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertFalse(user.is_staff)

    def test_staff_roles_get_admin_access(self):
        user = User.objects.create_user("agent@example.com", "x", role=User.Role.AGENT)
        self.assertTrue(user.is_staff)
        user.role = User.Role.CLIENT
        user.save()
        self.assertFalse(user.is_staff)

    def test_superuser_is_super_admin(self):
        user = User.objects.create_superuser("admin@example.com", "x")
        self.assertEqual(user.role, User.Role.SUPER_ADMIN)
        self.assertTrue(user.is_staff)
