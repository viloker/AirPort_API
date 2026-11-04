from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import SeatType
from airport.serializers import SeatTypeSerializer
from airport.tests.utils import create_seat_types
from airport.tests.tests_airport_api.helper import (
    create_admin,
    create_user,
    detail_url,
)

SEAT_TYPE_URL = reverse("airport:seattype-list")


class AnonymousSeatTypeAPITest(APITestCase):

    def test_anonymous_can_list_seat_types(self):
        create_seat_types(2)

        response = self.client.get(SEAT_TYPE_URL, format="json")

        serializer = SeatTypeSerializer(SeatType.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_cannot_create_seat_type(self):
        response = self.client.post(
            SEAT_TYPE_URL, data={"name": "Economy"}, format="json"
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(SeatType.objects.exists())

    def test_filter_seat_type_by_name(self):
        create_seat_types(3)
        seat_type = SeatType.objects.create(name="test")
        serializer = SeatTypeSerializer(seat_type)

        url = SEAT_TYPE_URL + "?name=test"
        response = self.client.get(url, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(serializer.data, response.data[0])


class UserSeatTypeAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_user())

    def test_user_can_list_seat_types(self):
        response = self.client.get(SEAT_TYPE_URL, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_seat_type(self):
        response = self.client.post(
            SEAT_TYPE_URL, data={"name": "Economy"}, format="json"
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(SeatType.objects.exists())

    def test_user_cannot_delete_seat_type(self):
        seat_type = create_seat_types(1)[0]

        response = self.client.delete(detail_url("seattype", seat_type.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(SeatType.objects.filter(id=seat_type.id).exists())


class AdminSeatTypeAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_admin())

    def test_admin_can_create_seat_type(self):
        response = self.client.post(
            SEAT_TYPE_URL, data={"name": "Economy"}, format="json"
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, SeatType.objects.count())

    def test_admin_can_update_seat_type(self):
        seat_type = create_seat_types(1)[0]

        response = self.client.patch(
            detail_url("seattype", seat_type.id),
            data={"name": "Business"},
            format="json",
        )

        seat_type.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("Business", seat_type.name)

    def test_admin_can_delete_seat_type(self):
        seat_type = create_seat_types(1)[0]

        response = self.client.delete(detail_url("seattype", seat_type.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(SeatType.objects.exists())
