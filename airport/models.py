from django.db import models
from django.core.exceptions import ValidationError

from phonenumber_field.modelfields import PhoneNumberField


class Airport(models.Model):
    name = models.CharField(max_length=64)
    last_code = models.CharField(max_length=64)
    closest_big_city = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Airport, related_name="sources", on_delete=models.PROTECT
    )
    destination = models.ForeignKey(
        Airport, related_name="distinations", on_delete=models.PROTECT
    )
    distance = models.PositiveSmallIntegerField()


class AirplaneType(models.Model):

    name = models.CharField(max_length=32)


class Airline(models.Model):
    name = models.CharField(max_length=64)


class Airplane(models.Model):
    name = models.CharField(max_length=64)

    rows = models.PositiveSmallIntegerField()
    seat_in_row = models.PositiveSmallIntegerField()

    airplane_type = models.ForeignKey(
        AirplaneType, related_name="airplanes", on_delete=models.SET_NULL, null=True
    )
    airline = models.ForeignKey(
        Airline, related_name="airplanes", on_delete=models.PROTECT
    )

    @property
    def total_seats(self):
        return self.rows * self.seat_in_row


class SeatType(models.Model):
    name = models.CharField(max_length=16)


class AirplaneSection(models.Model):

    airplane = models.ForeignKey(
        Airplane, related_name="sections", on_delete=models.CASCADE
    )

    seat_class = models.ForeignKey(
        SeatType, related_name="sections", default="Ecco", on_delete=models.SET_DEFAULT
    )
    row_from = models.PositiveSmallIntegerField()
    row_to = models.PositiveSmallIntegerField()

    def clean(self, *args, **kwargs):
        if not self.row_to <= self.airplane.rows:
            raise ValidationError("row_to can't be more than all seats in airplane")
        if not self.row_to > self.row_from:
            raise ValidationError("row_to can't be less than row_from")
        

class FlightStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    DELAYED = "delayed", "Delayed"
    BOARDING = "boarding", "Boarding"
    DEPARTED = "departed", "Departed"
    ARRIVED = "arrived", "Arrived"
    CANCELLED = "cancelled", "Cancelled"


class Flight(models.Model):

    flight_number = models.CharField(max_length=16)
    route = models.ForeignKey(Route, related_name="flights", on_delete=models.PROTECT)
    airplane = models.ForeignKey(
        Airplane, related_name="airplans", on_delete=models.PROTECT
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=16, choices=FlightStatus.choices, default=FlightStatus.SCHEDULED
    )
    crew = models.ManyToManyField("Crew", related_name="flights")


class CrewPosition(models.Model):
    name = models.CharField(max_length=32)


class Crew(models.Model):
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    email = models.EmailField(null=True, blank=True)
    number_phone = PhoneNumberField(null=True, blank=True)
    birth_data = models.DateField()

    position = models.ForeignKey(
        CrewPosition,
        related_name="crew_set",
        default="Worker",
        on_delete=models.SET_DEFAULT,
    )
