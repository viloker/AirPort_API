from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse

from airport.models import Airplane, Crew, CrewPosition


def detail_url(name: str, obj_id: int) -> str:
    return reverse(f"airport:{name}-detail", args=[obj_id])


def create_user():
    return get_user_model().objects.create_user(
        email="user@test.com", password="password123"
    )


def create_admin():
    return get_user_model().objects.create_superuser(
        email="admin@test.com", password="password123"
    )


def sample_airplane(**params) -> Airplane:
    defaults = {"name": "Boeing 737", "rows": 20, "seat_in_row": 6}
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_crew_member(**params) -> Crew:
    position, _ = CrewPosition.objects.get_or_create(name="Pilot")
    defaults = {
        "first_name": "John",
        "last_name": "Doe",
        "birth_date": date(1990, 1, 1),
        "position": position,
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)
