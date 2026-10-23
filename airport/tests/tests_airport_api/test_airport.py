from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

from airport.models import (
    Airport,
)

from airport.serializers import AirportSerializer

from airport.tests.utils import create_airports


class AnonymousAirportAPITest(APITestCase):

    def setUp(self):
        self.url = reverse("airport:airport-list")

    def test_anonymous_can_list_airport(self):
        response = self.client.get(self.url, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_anonymous_cannot_create_airport(self):

        data = {"name": "test_name"}

        response = self.client.post(self.url, data=data, format="json")

        airports = Airport.objects.all()

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(0, airports.count())

    def test_filter_airport_by_name(self):

        create_airports(3)

        airport = Airport.objects.create(name="Paris")

        serializer = AirportSerializer(airport)

        url = self.url + "?name=paris"

        response = self.client.get(url, format="json")

        self.assertEqual(1, len(response.data))
        self.assertEqual(serializer.data, response.data[0])

    def test_filter_airport_by_code(self):

        create_airports(3)

        airport = Airport.objects.create(name="Paris", code="PRS")
        
        serializer = AirportSerializer(airport)
        
        url = self.url + "?code=prs"

        response = self.client.get(url, format="json")

        self.assertEqual(1, len(response.data))
        self.assertEqual(serializer.data, response.data[0])


class UserAirportAPITest(APITestCase):

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email="test123@test.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)

        self.url = reverse("airport:airport-list")

    def test_user_can_list_airport(self):

        response = self.client.get(self.url, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_airport(self):

        data = {"name": "test_name"}

        response = self.client.post(self.url, data=data, format="json")

        airports = Airport.objects.all()

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(0, airports.count())


class AdminAirportAPITest(APITestCase):

    def setUp(self):

        self.url = reverse("airport:airport-list")

        self.user = get_user_model().objects.create_superuser(
            email="test@test.com", password="password"
        )

        self.client.force_authenticate(user=self.user)

    def test_admin_can_list_airport(self):

        response = self.client.get(self.url, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_admin_can_create_airport(self):

        data = {"name": "test_name"}

        response = self.client.post(self.url, data=data, format="json")

        airports = Airport.objects.all()

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, airports.count())
