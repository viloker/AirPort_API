from datetime import date, timedelta, datetime

from django.test import TestCase

from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from django.contrib.auth import get_user_model

from orders.models import PromoCode, Passenger, Ticket, Order

from airport.models import Flight
from airport.tests.utils import create_routes, create_airplanes


class PromoCodeTest(TestCase):

    def test_code_is_unique(self):
        code = "test_code"
        PromoCode.objects.create(
            code=code,
            discount_percent=50,
            valid_from=date(2024, 1, 1),
            valid_to=date(2025, 12, 12),
        )
        with self.assertRaises(IntegrityError):
            PromoCode.objects.create(
                code=code,
                discount_percent=50,
                valid_from=date(2024, 1, 1),
                valid_to=date(2025, 12, 12),
            )

    def test_valid_from_can_not_be_more_than_valid_to(self):
        with self.assertRaises(ValidationError):
            PromoCode.objects.create(
                code="test_code",
                discount_percent=50,
                valid_from=date(2024, 1, 1),
                valid_to=date(2023, 12, 31),
            )

    def test_discount_percent_max_value_100(self):
        with self.assertRaises(ValidationError):
            PromoCode.objects.create(
                code="test_code",
                discount_percent=200,
                valid_from=date(2024, 1, 1),
                valid_to=date(2025, 1, 1),
            )

    def test_discount_percent_min_value_1(self):
        with self.assertRaises(ValidationError):
            PromoCode.objects.create(
                code="test_code",
                discount_percent=0,
                valid_from=date(2024, 1, 1),
                valid_to=date(2025, 1, 1),
            )

    def test_is_active_true(self):

        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date.today() - timedelta(days=1),
            valid_to=date.today() + timedelta(days=1),
        )

        self.assertTrue(promo_code.is_active)

    def test_is_active_false(self):

        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date(2024, 1, 1),
            valid_to=date(2025, 5, 5),
        )

        self.assertFalse(promo_code.is_active)

    def test_code_valid_only_one_day(self):
        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date.today(),
            valid_to=date.today(),
        )

        self.assertTrue(promo_code.is_active)

    def test_valid_from_in_future(self):
        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date.today() + timedelta(days=1),
            valid_to=date.today() + timedelta(days=10),
        )

        self.assertFalse(promo_code.is_active)


class PassengerTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            email="test@gmail.com", password="test_password"
        )

    def test_create_pessenger_seccessful(self):
        passenger = Passenger.objects.create(
            first_name="test", last_name="test", user=self.user
        )

        self.assertEqual(self.user, passenger.user)
        self.assertEqual(1, self.user.passengers.all().count())

    def test_delete_user_if_passenger_is_exist_seccessful(self):
        passenger = Passenger.objects.create(
            first_name="test", last_name="test", user=self.user
        )

        self.user.delete()

        with self.assertRaises(Passenger.DoesNotExist):
            passenger.refresh_from_db()


class TicketTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.route = create_routes(1)[0]
        cls.airplane = create_airplanes(1)[0]
        departure_time = datetime(2025, 5, 12, 12, 15)

        cls.flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(hours=2),
        )

        cls.user = get_user_model().objects.create_user(
            email="test@gmail.com", password="testpassword"
        )

        cls.order = Order.objects.create(user=cls.user)

        cls.passenger = Passenger.objects.create(
            first_name="test", last_name="test", user=cls.user
        )

    def test_cannot_delete_flight_with_tickets(self):
        Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=2,
            price=200,
            order=self.order,
            passenger=self.passenger,
        )

        with self.assertRaises(ProtectedError):
            self.flight.delete()

    def test_seat_cannot_be_booked_twice_on_same_flight(self):
        passenger_1 = Passenger.objects.create(
            first_name="test_1", last_name="test_1", user=self.user
        )
        passenger_2 = Passenger.objects.create(
            first_name="test_2", last_name="test_2", user=self.user
        )

        Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=2,
            price=200,
            order=self.order,
            passenger=passenger_1,
        )
        with self.assertRaises(IntegrityError):
            Ticket.objects.create(
                flight=self.flight,
                row=2,
                seat=2,
                price=200,
                order=self.order,
                passenger=passenger_2,
            )

    def test_delete_order_deletes_tickets(self):
        ticket = Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=2,
            price=200,
            order=self.order,
            passenger=self.passenger,
        )

        self.order.delete()
        with self.assertRaises(Ticket.DoesNotExist):
            ticket.refresh_from_db()
    
    def test_delete_passenger_raises_error(self):
        Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=2,
            price=200,
            order=self.order,
            passenger=self.passenger,
        )

        with self.assertRaises(ProtectedError):
            self.passenger.delete()

    def test_related_names(self):
        ticket = Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=2,
            price=200,
            order=self.order,
            passenger=self.passenger
        )

        self.assertIn(ticket, self.flight.tickets.all())
        self.assertIn(ticket, self.order.tickets.all())
        self.assertIn(ticket, self.passenger.tickets.all())

    def test_one_passenger_on_2_seats(self):
        ticket_1 = Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=1,
            price=200,
            order=self.order,
            passenger=self.passenger
        )

        ticket_2 = Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=2,
            price=200,
            order=self.order,
            passenger=self.passenger
        )

        self.assertEqual(2, self.order.tickets.all().count())

    def test_same_seat_in_other_flight(self):

        departure_time = datetime(2025, 3, 30, 5, 40)
        flight_2 = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(hours=2)
        )

        ticket_1 = Ticket.objects.create(
            flight=self.flight,
            row=2,
            seat=1,
            price=200,
            order=self.order,
            passenger=self.passenger
        )

        ticket_2 = Ticket.objects.create(
            flight=flight_2,
            row=2,
            seat=1,
            price=200,
            order=self.order,
            passenger=self.passenger
        )

        self.assertIn(ticket_1, self.order.tickets.all())
        self.assertIn(ticket_2, self.order.tickets.all())

#