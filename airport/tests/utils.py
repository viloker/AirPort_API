import random
from datetime import datetime

from django.test import TestCase

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
    FlightStatus,
)


def create_airports(num: int) -> list[Airport]:
    return [
        Airport.objects.create(
            name=f"TestAirport_{i}",
            code=f"cod{i}",
            closest_big_city=f"City_{i}",
        )
        for i in range(num)
    ]


def create_routes(num: int) -> list[Route]:
    airports = create_airports(num * 2)
    middle = len(airports) // 2
    return [
        Route.objects.create(
            source=airport_sets[0], destination=airport_sets[1], distance=1000
        )
        for airport_sets in zip(airports[middle:], airports[:middle])
    ]


def create_airplane_types(num: int) -> list[AirplaneType]:
    return [AirplaneType.objects.create(name=f"Airplane_type{i}") for i in range(num)]


def create_airlines(num: int) -> list[Airline]:
    return [Airline.objects.create(name=f"Airline_{i}") for i in range(num)]


def create_airplanes(num: int) -> list[Airplane]:

    rows_list = [10, 15, 20, 25]
    seat_in_row_list = [4, 6, 8]

    return [
        Airplane.objects.create(
            name=f"Name_{i}",
            rows=random.choice(rows_list),
            seat_in_row=random.choice(seat_in_row_list),
        )
        for i in range(num)
    ]


def create_seat_types(num: int) -> list[SeatType]:
    return [SeatType.objects.create(name=f"SeatType_{i}") for i in range(num)]


def create_airplane_section() -> AirplaneSection:
    airplane = create_airplanes(1)[0]
    seat_type = create_seat_types(1)[0]

    return AirplaneSection.objects.create(
        airplane=airplane,
        seat_type=seat_type,
        row_from=1,
        row_to=5,
    )


def creete_flight_without_crew(num: int): ...


def create_flight_wiht_crew(num: int): ...


def create_crew_positions(num: int) -> list[CrewPosition]:
    return [CrewPosition.objects.create(name=f"Test_position_{i}") for i in range(num)]


def create_crews(num: int, position_list) -> list[Crew]:
    return [
        Crew.objects.create(
            first_name=f"Test_name_{i}",
            last_name=f"Test_{i}",
            birth_data=datetime.today(),
            position=random.choice(position_list),
        )
        for i in range(num)
    ]
