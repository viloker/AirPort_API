from django.test import TestCase

from django.contrib.auth import get_user_model


class UserTest(TestCase):

    def test_create_user_seccessfully(self):
        email = "testemail@test.com"
        password = "test_password"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertNotEqual(user.password, password)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)

    def test_create_super_user_eccessfully(self):
        email = "testemail@test.com"
        password = "test_password"
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )
        self.assertEqual(user.is_staff, True)
        self.assertEqual(user.is_superuser, True)
