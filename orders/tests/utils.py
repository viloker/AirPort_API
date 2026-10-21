from datetime import datetime, timedelta

from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model

from airport.tests.utils import create_routes, create_airplanes
from orders.models import Flight, Order, Passenger, Ticket


def create_ticket(order, price):
    route = create_routes(1)[0]
    airplane = create_airplanes(1)[0]
    departure_time = make_aware(datetime(2025, 5, 12, 12, 15))

    flight = Flight.objects.create(
        route=route,
        airplane=airplane,
        departure_time=departure_time,
        arrival_time=departure_time + timedelta(hours=2),
    )

    passenger = Passenger.objects.create(first_name="test", last_name="test", user=order.user)
    return Ticket.objects.create(
        flight=flight,
        row=2,
        seat=2,
        price=price,
        order=order,
        passenger=passenger,
    )
