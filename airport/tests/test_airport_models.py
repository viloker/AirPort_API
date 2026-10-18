from datetime import datetime

from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from airport.models import (
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Airline,
    SeatType,
    AirplaneSection,
    Flight,
    Crew,
    CrewPosition,
)

from airport.tests.utils import (
    create_airports,
    create_seat_types,
    create_airplanes,
    create_routes,
)


class AirportTest(TestCase):

    def setUp(self):
        self.name = "Test_1"
        self.code = "tst1"
        closest_big_city = "Test_city_1"
        self.airport_1 = Airport.objects.create(
            name=self.name, code=self.code, closest_big_city=closest_big_city
        )

    def test_airport_name_is_unique(self):

        with self.assertRaises(IntegrityError):
            Airport.objects.create(name=self.name)

    def test_airport_code_is_unique(self):

        with self.assertRaises(IntegrityError):
            Airport.objects.create(
                name="test",
                code=self.code,
            )

    def test_airport_code_unique_case_insensitive(self):
        code_2 = self.code.upper()

        with self.assertRaises(IntegrityError):
            Airport.objects.create(name="test", code=code_2)


class RouteTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.airports = create_airports(4)

    def test_source_and_destination_is_the_same_raise_error(self):
        airport = self.airports[0]

        with self.assertRaises(ValidationError):
            Route.objects.create(source=airport, destination=airport, distance=2000)

    def test_delete_airport_with_route_raises_error(self):
        Route.objects.create(
            source=self.airports[0], destination=self.airports[1], distance=2000
        )

        with self.assertRaises(ProtectedError):
            self.airports[0].delete()


class AirplaneTypeTest(TestCase):

    def test_airplane_type_is_unique(self):
        name = "test"

        AirplaneType.objects.create(name=name)

        with self.assertRaises(IntegrityError):
            AirplaneType.objects.create(name=name)


class AirlineTest(TestCase):

    def test_airline_name_is_unique(self):
        name = "test"

        Airline.objects.create(name=name)

        with self.assertRaises(IntegrityError):
            Airline.objects.create(name=name)


class AirplaneTest(TestCase):

    def test_airplane_name_is_unique(self):

        Airplane.objects.create(name="name", rows=5, seat_in_row=6)

        with self.assertRaises(IntegrityError):
            Airplane.objects.create(name="name", rows=5, seat_in_row=6)

    def test_airplane_rows_is_0(self):
        with self.assertRaises(IntegrityError):
            Airplane.objects.create(name="name", rows=0, seat_in_row=6)

    def test_airplane_seats_in_row_is_0(self):
        with self.assertRaises(IntegrityError):
            Airplane.objects.create(name="name", rows=5, seat_in_row=0)

    def test_total_seat_in_airplane(self):
        airplane = Airplane.objects.create(name="name", rows=5, seat_in_row=6)

        self.assertEqual(30, airplane.total_seats)

    def test_deleted_airplane_type_sets_null(self):
        airplane_type = AirplaneType.objects.create(name="test_type")
        airplane = Airplane.objects.create(
            name="test", rows=5, seat_in_row=5, airplane_type=airplane_type
        )
        airplane_type.delete()
        airplane.refresh_from_db()

        self.assertEqual(None, airplane.airplane_type)

    def test_delete_airline_raise_error(self):
        airline = Airline.objects.create(name="test")
        Airplane.objects.create(name="test", rows=5, seat_in_row=5, airline=airline)

        with self.assertRaises(ProtectedError):
            airline.delete()


class SeatTypeTest(TestCase):

    def test_seat_type_is_unique(self):
        name = "test"

        SeatType.objects.create(name=name)

        with self.assertRaises(IntegrityError):
            SeatType.objects.create(name=name)


class AirplaneSectionTest(TestCase):

    def test_row_from_more_than_row_to(self):
        airplane = create_airplanes(1)[0]

        with self.assertRaises(ValueError):
            AirplaneSection.objects.create(airplane=airplane, row_from=5, row_to=2)

    def test_delete_airplane_deletes_sections(self):
        airplane = create_airplanes(1)[0]

        airplane_section = AirplaneSection.objects.create(
            airplane=airplane, row_from=1, row_to=5
        )

        airplane.delete()
        with self.assertRaises(airplane_section.DoesNotExist):
            airplane_section.refresh_from_db()

    def test_delete_seat_type_raises_error(self):
        airplane = create_airplanes(1)[0]
        seat_type = create_seat_types(1)[0]

        AirplaneSection.objects.create(
            airplane=airplane, seat_type=seat_type, row_from=1, row_to=5
        )
        with self.assertRaises(ProtectedError):
            seat_type.delete()


class FlightTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.route = create_routes(1)[0]
        cls.airplane = create_airplanes(1)[0]
        dep_time = datetime(2024, 12, 12, 23, 16)
        arrival_time = datetime(2024, 12, 13, 1, 10)

        cls.flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane,
            departure_time=dep_time,
            arrival_time=arrival_time,
        )

    def test_delete_route_raises_error(self):

        with self.assertRaises(ProtectedError):
            self.route.delete()

    def test_delete_airplane_raise_error(self):

        with self.assertRaises(ProtectedError):
            self.airplane.delete()

    def test_default_status_of_flight(self):
        self.assertEqual("scheduled", self.flight.status)


class CrewPositionTest(TestCase):

    def test_crew_position_is_unique(self):
        name = "test"

        CrewPosition.objects.create(name=name)

        with self.assertRaises(IntegrityError):
            CrewPosition.objects.create(name=name)


class CrewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.email = "test@gmail.com"
        cls.number_phone = "+4915123456789"
        cls.position = CrewPosition.objects.create(name="test_position")
        cls.crew_member = Crew.objects.create(
            first_name="test_name",
            last_name="last_test_name",
            email=cls.email,
            number_phone=cls.number_phone,
            birth_date=datetime.today(),
            position=cls.position,
        )

    def test_email_is_unique(self):
        with self.assertRaises(IntegrityError):
            Crew.objects.create(
                first_name="test_name_2",
                last_name="last_test_name_2",
                email=self.email,
                birth_date=datetime.today(),
                position=self.position,
            )

    def test_phone_number_is_unique(self):
        with self.assertRaises(IntegrityError):
            Crew.objects.create(
                first_name="test_name_2",
                last_name="last_test_name_2",
                email="other@gmail.com",
                number_phone="+4915123456789",
                birth_date=datetime.today(),
                position=self.position,
            )

    def test_delete_position_raise_error(self):
        with self.assertRaises(ProtectedError):
            self.position.delete()

    def test_unique_of_crew_member(self):
        with self.assertRaises(IntegrityError):
            Crew.objects.create(
                first_name="test_name",
                last_name="last_test_name",
                birth_date=datetime.today(),
                position=self.position,
            )
