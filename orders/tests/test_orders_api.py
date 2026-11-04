import itertools
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import (
    Airport,
    Route,
    Airplane,
    SeatType,
    AirplaneSection,
    Flight,
    FlightStatus,
)
from orders.models import PromoCode, Passenger, Ticket, Order

ORDER_URL = reverse("orders:order-list")
PASSENGER_URL = reverse("orders:passenger-list")
PROMO_CODE_URL = reverse("orders:promocode-list")


def order_detail_url(order_id: int) -> str:
    return reverse("orders:order-detail", args=[order_id])


def passenger_detail_url(passenger_id: int) -> str:
    return reverse("orders:passenger-detail", args=[passenger_id])


_counter = itertools.count()


def unique(prefix: str) -> str:
    return f"{prefix}_{next(_counter)}"


def create_user(**params):
    defaults = {"email": f"{unique('user')}@test.com", "password": "password123"}
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def create_flight(
    departure_time=None,
    status=FlightStatus.SCHEDULED,
    price=Decimal("100.00"),
) -> Flight:

    route = Route.objects.create(
        source=Airport.objects.create(name=unique("Source")),
        destination=Airport.objects.create(name=unique("Destination")),
        distance=500,
    )
    airplane = Airplane.objects.create(name=unique("Plane"), rows=10, seat_in_row=6)

    business, _ = SeatType.objects.get_or_create(name="Business")
    economy, _ = SeatType.objects.get_or_create(name="Economy")
    AirplaneSection.objects.create(
        airplane=airplane, seat_type=business, row_from=1, row_to=2
    )
    AirplaneSection.objects.create(
        airplane=airplane, seat_type=economy, row_from=3, row_to=9
    )

    departure_time = departure_time or timezone.now() + timedelta(days=7)

    return Flight.objects.create(
        route=route,
        airplane=airplane,
        departure_time=departure_time,
        arrival_time=departure_time + timedelta(minutes=70),
        status=status,
        price=price,
    )


def create_passenger(user, **params) -> Passenger:
    defaults = {"first_name": "John", "last_name": "Doe"}
    defaults.update(params)
    return Passenger.objects.create(user=user, **defaults)


def create_order_with_ticket(user, flight, row=5, seat=1) -> Order:

    order = Order.objects.create(user=user)
    Ticket.objects.create(
        order=order,
        flight=flight,
        row=row,
        seat=seat,
        seat_class="Economy",
        price=flight.price,
        passenger=create_passenger(user),
    )
    return order


class OrderAPITestBase(APITestCase):

    def setUp(self):
        self.user = create_user()
        self.other_user = create_user()
        self.flight = create_flight()
        self.passenger = create_passenger(self.user)

        self.client.force_authenticate(user=self.user)

    def ticket(self, **params) -> dict:
        data = {
            "flight": self.flight.id,
            "row": 5,
            "seat": 1,
            "passenger": self.passenger.id,
        }
        data.update(params)
        return data

    def post_order(self, tickets, **params):
        data = {"tickets": tickets}
        data.update(params)
        return self.client.post(ORDER_URL, data=data, format="json")


class AnonymousOrderAPITest(APITestCase):

    def test_anonymous_cannot_list_orders(self):
        response = self.client.get(ORDER_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_anonymous_cannot_create_order(self):
        response = self.client.post(ORDER_URL, data={"tickets": []}, format="json")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_anonymous_cannot_list_passengers(self):
        response = self.client.get(PASSENGER_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


class OrderCreateAPITest(OrderAPITestBase):

    def test_create_order_with_tickets(self):
        response = self.post_order([self.ticket(seat=1), self.ticket(seat=2)])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        order = Order.objects.get()
        self.assertEqual(self.user, order.user)
        self.assertEqual(2, order.tickets.count())

    def test_price_and_seat_class_are_set_by_server(self):
        response = self.post_order([self.ticket(row=1, seat=1)])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        ticket = Ticket.objects.get()
        self.assertEqual(self.flight.price, ticket.price)
        self.assertEqual("Business", ticket.seat_class)

    def test_client_cannot_set_own_price(self):
        response = self.post_order([self.ticket(price="0.01", seat_class="Business")])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        ticket = Ticket.objects.get()
        self.assertEqual(self.flight.price, ticket.price)
        self.assertEqual("Economy", ticket.seat_class)

    def test_client_cannot_set_order_status(self):
        response = self.post_order([self.ticket()], status="paid")

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual("pending", Order.objects.get().status)

    def test_create_response_has_detail_format(self):
        response = self.post_order([self.ticket(row=1, seat=1)])

        ticket = response.data["tickets"][0]
        self.assertEqual("Business", ticket["seat_class"])
        self.assertEqual("100.00", ticket["price"])
        self.assertIn("passenger", ticket)
        self.assertEqual("100.00", response.data["total_price"])

    def test_create_order_with_active_promo_code(self):
        PromoCode.objects.create(
            code="AUTUMN10",
            discount_percent=10,
            valid_to=date.today() + timedelta(days=30),
        )

        response = self.post_order(
            [self.ticket(seat=1), self.ticket(seat=2)], promo_code="AUTUMN10"
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual("AUTUMN10", response.data["promo_code"])
        self.assertEqual("180.00", response.data["total_price"])


class OrderCreateValidationAPITest(OrderAPITestBase):

    def assertNothingCreated(self):
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Ticket.objects.exists())

    def test_order_without_tickets_returns_400(self):
        response = self.post_order([])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("tickets", response.data)
        self.assertNothingCreated()

    def test_taken_seat_returns_400(self):
        create_order_with_ticket(self.other_user, self.flight, row=5, seat=1)

        response = self.post_order([self.ticket(row=5, seat=1)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("seat", response.data["tickets"][0])
        self.assertEqual(1, Order.objects.count())

    def test_same_seat_twice_in_one_order_returns_400(self):
        response = self.post_order([self.ticket(seat=1), self.ticket(seat=1)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("tickets", response.data)
        self.assertNothingCreated()

    def test_same_seat_on_different_flights_is_allowed(self):
        other_flight = create_flight()

        response = self.post_order(
            [self.ticket(seat=1), self.ticket(flight=other_flight.id, seat=1)]
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_row_out_of_airplane_returns_400(self):
        response = self.post_order([self.ticket(row=11)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("row", response.data["tickets"][0])
        self.assertNothingCreated()

    def test_seat_out_of_row_returns_400(self):
        response = self.post_order([self.ticket(seat=7)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("seat", response.data["tickets"][0])
        self.assertNothingCreated()

    def test_row_and_seat_zero_return_400(self):
        response = self.post_order([self.ticket(row=0, seat=0)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertNothingCreated()

    def test_row_without_seat_class_returns_400(self):
        response = self.post_order([self.ticket(row=10)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("row", response.data["tickets"][0])
        self.assertNothingCreated()

    def test_passenger_of_another_user_returns_400(self):
        foreign_passenger = create_passenger(self.other_user)

        response = self.post_order([self.ticket(passenger=foreign_passenger.id)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("passenger", response.data["tickets"][0])
        self.assertNothingCreated()

    def test_departed_flight_returns_400(self):
        past_flight = create_flight(departure_time=timezone.now() - timedelta(hours=1))

        response = self.post_order([self.ticket(flight=past_flight.id)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("flight", response.data["tickets"][0])
        self.assertNothingCreated()

    def test_cancelled_flight_returns_400(self):
        cancelled = create_flight(status=FlightStatus.CANCELLED)

        response = self.post_order([self.ticket(flight=cancelled.id)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("flight", response.data["tickets"][0])
        self.assertNothingCreated()

    def test_delayed_flight_can_be_booked(self):
        delayed = create_flight(status=FlightStatus.DELAYED)

        response = self.post_order([self.ticket(flight=delayed.id)])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_one_invalid_ticket_creates_nothing(self):
        response = self.post_order([self.ticket(seat=1), self.ticket(seat=99)])

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({1}, set(response.data["tickets"]))
        self.assertIn("seat", response.data["tickets"][1])
        self.assertNothingCreated()

    def test_inactive_promo_code_returns_400(self):
        PromoCode.objects.create(
            code="OLD",
            discount_percent=10,
            valid_from=date.today() - timedelta(days=30),
            valid_to=date.today() - timedelta(days=1),
        )

        response = self.post_order([self.ticket()], promo_code="OLD")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("promo_code", response.data)
        self.assertNothingCreated()

    def test_unknown_promo_code_returns_400(self):
        response = self.post_order([self.ticket()], promo_code="NOPE")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("promo_code", response.data)
        self.assertNothingCreated()


class OrderVisibilityAPITest(OrderAPITestBase):

    def test_user_sees_only_own_orders(self):
        own = create_order_with_ticket(self.user, self.flight, seat=1)
        create_order_with_ticket(self.other_user, self.flight, seat=2)

        response = self.client.get(ORDER_URL)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([own.id], [order["id"] for order in response.data])

    def test_user_cannot_retrieve_foreign_order(self):
        foreign = create_order_with_ticket(self.other_user, self.flight)

        response = self.client.get(order_detail_url(foreign.id))

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_admin_sees_all_orders(self):
        create_order_with_ticket(self.user, self.flight, seat=1)
        create_order_with_ticket(self.other_user, self.flight, seat=2)
        admin = get_user_model().objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.client.force_authenticate(user=admin)

        response = self.client.get(ORDER_URL)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_list_ticket_has_route_and_duration(self):
        create_order_with_ticket(self.user, self.flight)

        response = self.client.get(ORDER_URL)

        ticket = response.data[0]["tickets"][0]
        self.assertEqual(self.flight.route.source.name, ticket["source"])
        self.assertEqual(self.flight.route.destination.name, ticket["destination"])
        self.assertEqual(70, ticket["duration"])

    def test_orders_cannot_be_updated_or_deleted(self):
        order = create_order_with_ticket(self.user, self.flight)

        patch = self.client.patch(
            order_detail_url(order.id), data={"status": "paid"}, format="json"
        )
        delete = self.client.delete(order_detail_url(order.id))

        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, patch.status_code)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, delete.status_code)
        self.assertTrue(Order.objects.filter(id=order.id).exists())


class PassengerAPITest(OrderAPITestBase):

    def test_user_sees_only_own_passengers(self):
        create_passenger(self.other_user)

        response = self.client.get(PASSENGER_URL)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([self.passenger.id], [p["id"] for p in response.data])

    def test_created_passenger_belongs_to_current_user(self):
        response = self.client.post(
            PASSENGER_URL,
            data={"first_name": "Anna", "last_name": "Schmidt"},
            format="json",
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.user, Passenger.objects.get(id=response.data["id"]).user)

    def test_user_cannot_retrieve_foreign_passenger(self):
        foreign = create_passenger(self.other_user)

        response = self.client.get(passenger_detail_url(foreign.id))

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)


class PromoCodeAPITest(APITestCase):

    def test_user_cannot_list_promo_codes(self):
        self.client.force_authenticate(user=create_user())

        response = self.client.get(PROMO_CODE_URL)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_valid_from_after_valid_to_returns_400(self):
        admin = get_user_model().objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.client.force_authenticate(user=admin)
        data = {
            "code": "BROKEN",
            "discount_percent": 10,
            "valid_from": "2026-12-10",
            "valid_to": "2026-12-01",
        }

        response = self.client.post(PROMO_CODE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertFalse(PromoCode.objects.exists())
