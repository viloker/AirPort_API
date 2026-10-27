from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import Airline
from airport.serializers import AirlineSerializer
from airport.tests.utils import create_airlines
from airport.tests.tests_airport_api.helper import (
    create_admin,
    create_user,
    detail_url,
)

AIRLINE_URL = reverse("airport:airline-list")


class AnonymousAirlineAPITest(APITestCase):

    def test_anonymous_can_list_airlines(self):
        create_airlines(2)

        response = self.client.get(AIRLINE_URL, format="json")

        serializer = AirlineSerializer(Airline.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_cannot_create_airline(self):
        response = self.client.post(
            AIRLINE_URL, data={"name": "Lufthansa"}, format="json"
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(Airline.objects.exists())

    def test_filter_airlines_by_name(self):

        create_airlines(3)
        airline_1 = Airline.objects.create(name="test_name_1")
        airline_2 = Airline.objects.create(name="test_name_2")
        serializer = AirlineSerializer([airline_1, airline_2], many=True)

        url = AIRLINE_URL + "?name=test"
        response = self.client.get(url, format="json")

        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)


class UserAirlineAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_user())

    def test_user_can_list_airlines(self):
        response = self.client.get(AIRLINE_URL, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_airline(self):
        response = self.client.post(
            AIRLINE_URL, data={"name": "Lufthansa"}, format="json"
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(Airline.objects.exists())

    def test_user_cannot_delete_airline(self):
        airline = create_airlines(1)[0]

        response = self.client.delete(detail_url("airline", airline.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(Airline.objects.filter(id=airline.id).exists())


class AdminAirlineAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_admin())

    def test_admin_can_create_airline(self):
        response = self.client.post(
            AIRLINE_URL, data={"name": "Lufthansa"}, format="json"
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, Airline.objects.count())

    def test_admin_can_update_airline(self):
        airline = create_airlines(1)[0]

        response = self.client.patch(
            detail_url("airline", airline.id), data={"name": "Eurowings"}, format="json"
        )

        airline.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("Eurowings", airline.name)

    def test_admin_can_delete_airline(self):
        airline = create_airlines(1)[0]

        response = self.client.delete(detail_url("airline", airline.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Airline.objects.exists())
