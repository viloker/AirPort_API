from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer
from airport.tests.utils import create_airplane_types
from airport.tests.tests_airport_api.helper import (
    create_admin,
    create_user,
    detail_url,
)

AIRPLANE_TYPE_URL = reverse("airport:airplanetype-list")


class AnonymousAirplaneTypeAPITest(APITestCase):

    def test_anonymous_can_list_airplane_types(self):
        create_airplane_types(2)

        response = self.client.get(AIRPLANE_TYPE_URL, format="json")

        serializer = AirplaneTypeSerializer(AirplaneType.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_cannot_create_airplane_type(self):
        response = self.client.post(
            AIRPLANE_TYPE_URL, data={"name": "Narrow-body"}, format="json"
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(AirplaneType.objects.exists())

    def test_filter_airplane_types_by_name(self):

        create_airplane_types(5)

        airplane_type = AirplaneType.objects.create(name="Airbus")

        serializer = AirplaneTypeSerializer(airplane_type)

        url = AIRPLANE_TYPE_URL + "?name=Airbus"
        response = self.client.get(url, format="json")

        self.assertEqual(1, len(response.data))
        self.assertEqual(serializer.data, response.data[0])

    def test_filter_airplane_types_with_not_valid_data(self):

        create_airplane_types(5)

        url = AIRPLANE_TYPE_URL + "?name=some_name"
        response = self.client.get(url, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([], response.data)

class UserAirplaneTypeAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_user())

    def test_user_can_list_airplane_types(self):
        response = self.client.get(AIRPLANE_TYPE_URL, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_airplane_type(self):
        response = self.client.post(
            AIRPLANE_TYPE_URL, data={"name": "Narrow-body"}, format="json"
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(AirplaneType.objects.exists())

    def test_user_cannot_delete_airplane_type(self):
        airplane_type = create_airplane_types(1)[0]

        response = self.client.delete(detail_url("airplanetype", airplane_type.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(AirplaneType.objects.filter(id=airplane_type.id).exists())


class AdminAirplaneTypeAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_admin())

    def test_admin_can_create_airplane_type(self):
        response = self.client.post(
            AIRPLANE_TYPE_URL, data={"name": "Narrow-body"}, format="json"
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, AirplaneType.objects.count())

    def test_admin_can_update_airplane_type(self):
        airplane_type = create_airplane_types(1)[0]

        response = self.client.patch(
            detail_url("airplanetype", airplane_type.id),
            data={"name": "Wide-body"},
            format="json",
        )

        airplane_type.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("Wide-body", airplane_type.name)

    def test_admin_can_delete_airplane_type(self):
        airplane_type = create_airplane_types(1)[0]

        response = self.client.delete(detail_url("airplanetype", airplane_type.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(AirplaneType.objects.exists())

    def test_duplicate_airplane_type_name_returns_400(self):
        AirplaneType.objects.create(name="Narrow-body")

        response = self.client.post(
            AIRPLANE_TYPE_URL, data={"name": "Narrow-body"}, format="json"
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(1, AirplaneType.objects.count())
