from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import AirplaneSection
from airport.serializers import AirplaneSectionSerializer
from airport.tests.utils import (
    create_seat_types,
    create_airplane_section,
    create_airplanes,
)
from airport.tests.tests_airport_api.helper import (
    create_admin,
    create_user,
    detail_url,
    sample_airplane,
)

AIRPLANE_SECTION_URL = reverse("airport:airplanesection-list")


class AnonymousAirplaneSectionAPITest(APITestCase):

    def test_anonymous_can_list_airplane_sections(self):
        create_airplane_section()

        response = self.client.get(AIRPLANE_SECTION_URL, format="json")

        serializer = AirplaneSectionSerializer(AirplaneSection.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_cannot_create_airplane_section(self):
        airplane = create_airplanes(1)[0]
        seat_type = create_seat_types(1)[0]
        data = {
            "airplane": airplane.id,
            "seat_type": seat_type.id,
            "row_from": 1,
            "row_to": 5,
        }

        response = self.client.post(AIRPLANE_SECTION_URL, data=data, format="json")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(AirplaneSection.objects.exists())

    def test_filter_airplane_sections_by_airplane(self):
        airplane_section = create_airplane_section()
        serializer = AirplaneSectionSerializer(airplane_section)
        airplane = airplane_section.airplane

        url = AIRPLANE_SECTION_URL + f"?airplane={airplane.id}"
        response = self.client.get(url, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertIn(serializer.data, response.data)


class UserAirplaneSectionAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_user())

    def test_user_can_list_airplane_sections(self):
        response = self.client.get(AIRPLANE_SECTION_URL, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_airplane_section(self):
        airplane = sample_airplane()
        seat_type = create_seat_types(1)[0]
        data = {
            "airplane": airplane.id,
            "seat_type": seat_type.id,
            "row_from": 1,
            "row_to": 5,
        }

        response = self.client.post(AIRPLANE_SECTION_URL, data=data, format="json")

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(AirplaneSection.objects.exists())

    def test_user_cannot_delete_airplane_section(self):
        section = create_airplane_section()

        response = self.client.delete(detail_url("airplanesection", section.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(AirplaneSection.objects.filter(id=section.id).exists())


class AdminAirplaneSectionAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_admin())

    def test_admin_can_create_airplane_section(self):
        airplane = create_airplanes(1)[0]
        seat_type = create_seat_types(1)[0]

        data = {
            "airplane": airplane.id,
            "seat_type": seat_type.id,
            "row_from": 1,
            "row_to": 5,
        }

        response = self.client.post(AIRPLANE_SECTION_URL, data=data, format="json")

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, AirplaneSection.objects.count())

    def test_admin_can_update_airplane_section(self):
        section = create_airplane_section()

        response = self.client.patch(
            detail_url("airplanesection", section.id),
            data={"row_to": 10},
            format="json",
        )

        section.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(10, section.row_to)

    def test_admin_can_delete_airplane_section(self):
        section = create_airplane_section()

        response = self.client.delete(detail_url("airplanesection", section.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(AirplaneSection.objects.exists())

    # def test_section_row_to_greater_than_airplane_rows_returns_400(self):

    #     data = {
    #         "airplane": self.airplane.id,
    #         "seat_type": self.seat_type.id,
    #         "row_from": 1,
    #         "row_to": 21,
    #     }

    #     response = self.client.post(AIRPLANE_SECTION_URL, data=data, format="json")

    #     self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
    #     self.assertFalse(AirplaneSection.objects.exists())

    # def test_section_row_to_less_than_row_from_returns_400(self):

    #     data = {
    #         "airplane": self.airplane.id,
    #         "seat_type": self.seat_type.id,
    #         "row_from": 10,
    #         "row_to": 5,
    #     }

    #     response = self.client.post(AIRPLANE_SECTION_URL, data=data, format="json")

    #     self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
    #     self.assertFalse(AirplaneSection.objects.exists())
