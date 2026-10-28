from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import CrewPosition
from airport.serializers import CrewPositionSerializer
from airport.tests.utils import create_crew_positions
from airport.tests.tests_airport_api.helper import (
    create_admin,
    create_user,
    detail_url,
)

CREW_POSITION_URL = reverse("airport:crewposition-list")


class AnonymousCrewPositionAPITest(APITestCase):

    def test_anonymous_can_list_crew_positions(self):
        create_crew_positions(2)

        response = self.client.get(CREW_POSITION_URL)

        serializer = CrewPositionSerializer(CrewPosition.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_can_retrieve_crew_position(self):
        position = create_crew_positions(1)[0]

        response = self.client.get(detail_url("crewposition", position.id))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CrewPositionSerializer(position).data, response.data)

    def test_anonymous_cannot_create_crew_position(self):
        response = self.client.post(
            CREW_POSITION_URL, data={"name": "Pilot"}, format="json"
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(CrewPosition.objects.exists())


class UserCrewPositionAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_user())

    def test_user_can_list_crew_positions(self):
        response = self.client.get(CREW_POSITION_URL)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_can_retrieve_crew_position(self):
        position = create_crew_positions(1)[0]

        response = self.client.get(detail_url("crewposition", position.id))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_crew_position(self):
        response = self.client.post(
            CREW_POSITION_URL, data={"name": "Pilot"}, format="json"
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(CrewPosition.objects.exists())

    def test_user_cannot_update_crew_position(self):
        position = create_crew_positions(1)[0]

        response = self.client.patch(
            detail_url("crewposition", position.id),
            data={"name": "Co-pilot"},
            format="json",
        )

        position.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertNotEqual("Co-pilot", position.name)

    def test_user_cannot_delete_crew_position(self):
        position = create_crew_positions(1)[0]

        response = self.client.delete(detail_url("crewposition", position.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(CrewPosition.objects.filter(id=position.id).exists())


class AdminCrewPositionAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_admin())

    def test_admin_can_list_crew_positions(self):
        create_crew_positions(2)

        response = self.client.get(CREW_POSITION_URL)

        serializer = CrewPositionSerializer(CrewPosition.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_admin_can_create_crew_position(self):
        response = self.client.post(
            CREW_POSITION_URL, data={"name": "Pilot"}, format="json"
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, CrewPosition.objects.count())

    def test_admin_can_update_crew_position(self):
        position = create_crew_positions(1)[0]

        response = self.client.patch(
            detail_url("crewposition", position.id),
            data={"name": "Co-pilot"},
            format="json",
        )

        position.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("Co-pilot", position.name)

    def test_admin_can_delete_crew_position(self):
        position = create_crew_positions(1)[0]

        response = self.client.delete(detail_url("crewposition", position.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(CrewPosition.objects.exists())

    def test_duplicate_crew_position_name_returns_400(self):
        CrewPosition.objects.create(name="Pilot")

        response = self.client.post(
            CREW_POSITION_URL, data={"name": "Pilot"}, format="json"
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(1, CrewPosition.objects.count())
