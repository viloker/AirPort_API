from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

REGISTER_URL = reverse("user:user_register")
TOKEN_URL = reverse("user:get_toket")
REFRESH_TOKEN_URL = reverse("user:refresh_token")
ME_URL = reverse("user:me")


class UserUrlsAPITests(APITestCase):

    def test_urls(self):
        self.assertEqual("/api/user/register/", REGISTER_URL)
        self.assertEqual("/api/user/token/", TOKEN_URL)
        self.assertEqual("/api/user/refresh-token/", REFRESH_TOKEN_URL)
        self.assertEqual("/api/user/me/", ME_URL)


class PablicUserAPITests(APITestCase):

    def setUp(self):
        self.playload = {
            "email": "test@test.com",
            "password": "test_password",
            "first_name": "test_name",
            "last_name": "test_last_name",
            "number_phone": "+4915123456789",
        }

    def test_register_user_seccessful(self):
        response = self.client.post(REGISTER_URL, self.playload, format="json")
        user = get_user_model().objects.get(email="test@test.com")

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertTrue(user.check_password(self.playload.get("password")))
        self.assertNotIn("password", response.data)

    def test_register_user_without_email(self):
        self.playload["email"] = ""
        response = self.client.post(REGISTER_URL, self.playload, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_register_user_without_password(self):
        self.playload["password"] = ""
        response = self.client.post(REGISTER_URL, self.playload, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_register_with_double_email(self):
        response = self.client.post(REGISTER_URL, self.playload, format="json")
        bad_response = self.client.post(REGISTER_URL, self.playload, format="json")
        users_count = get_user_model().objects.all().count()

        self.assertEqual(status.HTTP_400_BAD_REQUEST, bad_response.status_code)
        self.assertEqual(1, users_count)

    def test_get_user_token_seccessful(self):
        self.client.post(REGISTER_URL, self.playload)
        token_res = self.client.post(TOKEN_URL, self.playload)

        self.assertEqual(status.HTTP_200_OK, token_res.status_code)
        self.assertEqual(2, len(token_res.data))

    def test_get_token_with_wrong_password(self):
        self.playload["password"] = "wrong_password"

        token_res = self.client.post(TOKEN_URL, self.playload, format="json")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, token_res.status_code)

    def test_get_refresh_token_seccessful(self):
        self.client.post(REGISTER_URL, self.playload)
        token_res = self.client.post(TOKEN_URL, self.playload)

        self.playload["refresh"] = token_res.data.get("refresh")
        response = self.client.post(REFRESH_TOKEN_URL, self.playload)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn("access", container=response.data)


class PrivateUserAPITests(APITestCase):

    def setUp(self):
        self.playload = {"email": "test@test.com", "password": "test_password"}

        self.user = get_user_model().objects.create_user(**self.playload)

        self.client.force_authenticate(user=self.user)

    def test_retrive_me(self):

        response = self.client.get(ME_URL)
        data = {
            "email": "test@test.com",
            "first_name": None,
            "last_name": None,
            "number_phone": None,
        }
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(data, response.data)

    def test_patch_me_seccessful(self):
        response = self.client.patch(
            ME_URL, data={"email": "123@gmail.com"}, format="json"
        )
        self.user.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("123@gmail.com", self.user.email)

    def test_put_me_seccessful(self):
        response = self.client.put(
            ME_URL,
            data={
                "email": "123@gmail.com",
                "first_name": "test",
                "last_name": "test",
                "number_phone": "+4915123456789",
            },
            format="json",
        )

        self.user.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("123@gmail.com", self.user.email)
        self.assertEqual("test", self.user.first_name)
        self.assertEqual("test", self.user.last_name)
        self.assertEqual("+4915123456789", self.user.number_phone)

    def test_me_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(ME_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
