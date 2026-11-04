from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import Airplane
from airport.serializers import AirplaneSerializer
from airport.tests.utils import (
    create_airlines,
    create_airplane_types,
    create_airplanes,
)
from airport.tests.tests_airport_api.helper import (
    create_admin,
    create_user,
    detail_url,
    sample_airplane,
)

AIRPLANE_URL = reverse("airport:airplane-list")


class AnonymousAirplaneAPITest(APITestCase):

    def test_anonymous_can_list_airplanes(self):
        create_airplanes(2)

        response = self.client.get(AIRPLANE_URL, format="json")

        serializer = AirplaneSerializer(Airplane.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_can_retrieve_airplane_with_total_seats(self):
        airplane = sample_airplane(rows=20, seat_in_row=6)

        response = self.client.get(detail_url("airplane", airplane.id), format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(120, response.data["total_seats"])

    def test_anonymous_cannot_create_airplane(self):
        data = {"name": "Boeing 737", "rows": 20, "seat_in_row": 6}

        response = self.client.post(AIRPLANE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(Airplane.objects.exists())

    def test_filter_airplanes_by_name(self):
        boeing_737 = sample_airplane(name="Boeing 737")
        boeing_787 = sample_airplane(name="Boeing 787")
        sample_airplane(name="Airbus A320")

        serializer = AirplaneSerializer([boeing_737, boeing_787], many=True)

        response = self.client.get(AIRPLANE_URL + "?name=boeing", format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)

    def test_filter_airplanes_by_airline(self):
        airline_list = create_airlines(2)
        airline_1 = airline_list[0]
        airline_2 = airline_list[1]

        airplane_1 = sample_airplane(name="Plane_1", airline=airline_1)
        airplane_2 = sample_airplane(name="Plane_2", airline=airline_1)
        sample_airplane(name="Plane_3", airline=airline_2)

        serializer = AirplaneSerializer([airplane_1, airplane_2], many=True)

        response = self.client.get(
            AIRPLANE_URL + f"?airline={airline_1.id}", format="json"
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)

    def test_filter_airplanes_by_airplane_type(self):
        airline_types_list = create_airplane_types(2)
        airline_type_1 = airline_types_list[0]
        airline_type_2 = airline_types_list[1]

        airplane_1 = sample_airplane(name="Plane_1", airplane_type=airline_type_1)
        airplane_2 = sample_airplane(name="Plane_2", airplane_type=airline_type_1)
        sample_airplane(name="Plane_3", airplane_type=airline_type_2)

        serializer = AirplaneSerializer([airplane_1, airplane_2], many=True)

        response = self.client.get(
            AIRPLANE_URL + f"?airplane_type={airline_type_1.id}", format="json"
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)


class UserAirplaneAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_user())

    def test_user_can_list_airplanes(self):
        response = self.client.get(AIRPLANE_URL, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_airplane(self):
        data = {"name": "Boeing 737", "rows": 20, "seat_in_row": 6}

        response = self.client.post(AIRPLANE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(Airplane.objects.exists())

    def test_user_cannot_update_airplane(self):
        airplane = sample_airplane()

        response = self.client.patch(
            detail_url("airplane", airplane.id), data={"rows": 1}, format="json"
        )

        airplane.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(20, airplane.rows)

    def test_user_cannot_delete_airplane(self):
        airplane = sample_airplane()

        response = self.client.delete(detail_url("airplane", airplane.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(Airplane.objects.filter(id=airplane.id).exists())


class AdminAirplaneAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_admin())

    def test_admin_can_create_airplane(self):
        airplane_type = create_airplane_types(1)[0]
        airline = create_airlines(1)[0]
        data = {
            "name": "Boeing 737",
            "rows": 20,
            "seat_in_row": 6,
            "airplane_type": airplane_type.id,
            "airline": airline.id,
        }

        response = self.client.post(AIRPLANE_URL, data=data, format="json")

        airplane = Airplane.objects.get()
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(airline, airplane.airline)
        self.assertEqual(airplane_type, airplane.airplane_type)

    def test_admin_can_update_airplane(self):
        airplane = sample_airplane()

        response = self.client.patch(
            detail_url("airplane", airplane.id), data={"rows": 30}, format="json"
        )

        airplane.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(30, airplane.rows)

    def test_admin_can_delete_airplane(self):
        airplane = sample_airplane()

        response = self.client.delete(detail_url("airplane", airplane.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Airplane.objects.exists())

    def test_airplane_with_zero_rows_returns_400(self):
        data = {"name": "Boeing 737", "rows": 0, "seat_in_row": 6}

        response = self.client.post(AIRPLANE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("rows", response.data)
        self.assertFalse(Airplane.objects.exists())

    def test_airplane_with_zero_seats_in_row_returns_400(self):
        data = {"name": "Boeing 737", "rows": 20, "seat_in_row": 0}

        response = self.client.post(AIRPLANE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("seat_in_row", response.data)
        self.assertFalse(Airplane.objects.exists())
