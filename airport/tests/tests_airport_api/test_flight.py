from datetime import datetime, timedelta

from django.urls import reverse
from django.utils.timezone import make_aware
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import Flight, FlightStatus
from airport.serializers import FlightSerializer
from airport.tests.utils import create_routes, create_flight, create_airplanes
from airport.tests.tests_airport_api.helper import (
    create_admin,
    create_user,
    detail_url,
    sample_airplane,
    sample_crew_member,
)

FLIGHT_URL = reverse("airport:flight-list")


class AnonymousFlightAPITest(APITestCase):

    def test_anonymous_can_list_flights(self):
        create_flight()

        response = self.client.get(FLIGHT_URL, format="json")

        serializer = FlightSerializer(Flight.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_can_retrieve_flight(self):
        flight = create_flight()

        response = self.client.get(detail_url("flight", flight.id), format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(FlightSerializer(flight).data, response.data)

    def test_anonymous_cannot_create_flight(self):
        flight = create_flight()
        serializer = FlightSerializer(flight)
        flight.delete()

        response = self.client.post(FLIGHT_URL, data=serializer.data, format="json")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(Flight.objects.exists())

    def test_filter_flights_by_source(self):
        route_1, route_2 = create_routes(2)
        airplane = create_airplanes(1)[0]
        departure = timezone.now() + timedelta(days=1)

        flights = [
            Flight.objects.create(
                route=route,
                airplane=airplane,
                departure_time=departure,
                arrival_time=departure + timedelta(hours=2),
            )
            for route in (route_1, route_1, route_2)
        ]
        serializer = FlightSerializer(flights[:2], many=True)

        response = self.client.get(FLIGHT_URL + f"?source={route_1.source.id}")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)

    def test_filter_flights_by_destination(self):
        route_1, route_2 = create_routes(2)
        airplane = create_airplanes(1)[0]
        departure = timezone.now() + timedelta(days=1)

        flights = [
            Flight.objects.create(
                route=route,
                airplane=airplane,
                departure_time=departure,
                arrival_time=departure + timedelta(hours=2),
            )
            for route in (route_1, route_1, route_2)
        ]
        serializer = FlightSerializer(flights[:2], many=True)

        response = self.client.get(
            FLIGHT_URL + f"?destination={route_1.destination.id}"
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)

    def test_filter_flights_by_departure_date(self):
        route = create_routes(1)[0]
        airplane = create_airplanes(1)[0]
        target = (timezone.now() + timedelta(days=10)).replace(
            hour=12, minute=0, second=0, microsecond=0
        )

        departures = (
            target,
            target + timedelta(hours=3),
            target - timedelta(days=1),  # day before, must not be returned
            target + timedelta(days=1),  # day after, must not be returned
        )
        flights = [
            Flight.objects.create(
                route=route,
                airplane=airplane,
                departure_time=departure,
                arrival_time=departure + timedelta(hours=2),
            )
            for departure in departures
        ]
        serializer = FlightSerializer(flights[:2], many=True)

        target_day = timezone.localtime(target).date().isoformat()
        response = self.client.get(FLIGHT_URL + f"?departure={target_day}")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)

    def test_filter_flights_by_status(self):
        route = create_routes(1)[0]
        airplane = create_airplanes(1)[0]
        departure = timezone.now() + timedelta(days=1)

        statuses = (
            FlightStatus.DELAYED,
            FlightStatus.SCHEDULED,
            FlightStatus.CANCELLED,
        )
        flights = [
            Flight.objects.create(
                route=route,
                airplane=airplane,
                departure_time=departure,
                arrival_time=departure + timedelta(hours=2),
                status=flight_status,
            )
            for flight_status in statuses
        ]

        response = self.client.get(FLIGHT_URL + "?status=delayed")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(FlightSerializer(flights[0]).data, response.data[0])


class UserFlightAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_user())

    def test_user_can_list_flights(self):
        response = self.client.get(FLIGHT_URL, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_flight(self):
        flight = create_flight()
        serializer = FlightSerializer(flight)
        flight.delete()
        response = self.client.post(FLIGHT_URL, data=serializer.data, format="json")

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(Flight.objects.exists())

    def test_user_cannot_change_flight_status(self):
        flight = create_flight()

        response = self.client.patch(
            detail_url("flight", flight.id),
            data={"status": FlightStatus.CANCELLED},
            format="json",
        )

        flight.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(FlightStatus.SCHEDULED, flight.status)

    def test_user_cannot_delete_flight(self):
        flight = create_flight()

        response = self.client.delete(detail_url("flight", flight.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(Flight.objects.filter(id=flight.id).exists())


class AdminFlightAPITest(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=create_admin())

    def test_admin_can_create_flight(self):
        data = {
            "route": create_routes(1)[0].id,
            "airplane": sample_airplane(name="Airbus A320").id,
            "departure_time": make_aware(datetime(2024, 12, 12, 23, 16)),
            "arrival_time": make_aware(datetime(2024, 12, 13, 2, 16)),
            "crew": [sample_crew_member(first_name="Anna").id],
        }

        response = self.client.post(FLIGHT_URL, data=data, format="json")

        flight = Flight.objects.get()
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(FlightStatus.SCHEDULED, flight.status)
        self.assertEqual(data["crew"], list(flight.crew.values_list("id", flat=True)))

    def test_admin_can_change_flight_status(self):
        flight = create_flight()

        response = self.client.patch(
            detail_url("flight", flight.id),
            data={"status": FlightStatus.DELAYED},
            format="json",
        )

        flight.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(FlightStatus.DELAYED, flight.status)

    def test_admin_can_delete_flight(self):
        flight = create_flight()

        response = self.client.delete(detail_url("flight", flight.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Flight.objects.exists())

    def test_flight_with_unknown_status_returns_400(self):
        flight = create_flight()
        serializer = FlightSerializer(flight)
        flight.delete()

        data = serializer.data
        data["status"] = "lost"

        response = self.client.post(FLIGHT_URL, data=data, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("status", response.data)
        self.assertFalse(Flight.objects.exists())

    def test_flight_arrival_before_departure_returns_400(self):
        flight = create_flight()
        serializer = FlightSerializer(flight)
        flight.delete()

        data = serializer.data
        data["arrival_time"], data["departure_time"] = (
            data["departure_time"],
            data["arrival_time"],
        )

        response = self.client.post(FLIGHT_URL, data=data, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertFalse(Flight.objects.exists())
