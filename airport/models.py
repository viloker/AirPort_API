from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from phonenumber_field.modelfields import PhoneNumberField


class Airport(models.Model):
    name = models.CharField(max_length=64, unique=True)
    code = models.CharField(max_length=4, unique=True, null=True, blank=True)
    closest_big_city = models.CharField(max_length=64, null=True, blank=True)

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

    def __str__(self):
        return f"{self.source.name} -> {self.destination.name} "

    def clean(self, *args, **kwargs):
        if self.source == self.destination:
            raise ValidationError("Source city can't be the same like destination city")


class AirplaneType(models.Model):

    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class Airline(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=32, unique=True)

    rows = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    seat_in_row = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    airplane_type = models.ForeignKey(
        AirplaneType,
        related_name="airplanes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    airline = models.ForeignKey(
        Airline,
        related_name="airplanes",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    @property
    def total_seats(self):
        return self.rows * self.seat_in_row

    def __str__(self):
        return self.name


class SeatType(models.Model):
    name = models.CharField(max_length=16, unique=True)

    def __str__(self):
        return self.name


class AirplaneSection(models.Model):

    airplane = models.ForeignKey(
        Airplane, related_name="sections", on_delete=models.CASCADE
    )

    seat_type = models.ForeignKey(
        SeatType,
        related_name="sections",
        on_delete=models.PROTECT,
        null=True
    )
    row_from = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    row_to = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    def clean(self, *args, **kwargs):
        if not self.row_to <= self.airplane.rows:
            raise ValidationError("row_to can't be more than all seats in airplane")
        if not self.row_to > self.row_from:
            raise ValidationError("row_to can't be less than row_from")

    def __str__(self):
        return f"Seat type is '{self.seat_type.name}' in '{self.airplane.name}'"


class FlightStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    DELAYED = "delayed", "Delayed"
    BOARDING = "boarding", "Boarding"
    DEPARTED = "departed", "Departed"
    ARRIVED = "arrived", "Arrived"
    CANCELLED = "cancelled", "Cancelled"


class Flight(models.Model):

    # flight_number = models.CharField(max_length=16)
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

    def clean(self, *args, **kwargs): ...

    # тут можливо потрібно буде додати логіку для розрахунку часу

    def __str__(self):
        return f"Flight from {self.route.source.name} to {self.route.destination.name}, status: {self.status}"


class CrewPosition(models.Model):

    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    email = models.EmailField(null=True, blank=True, unique=True)
    number_phone = PhoneNumberField(null=True, blank=True, unique=True)
    birth_data = models.DateField()

    position = models.ForeignKey(
        CrewPosition,
        related_name="crew_set",
        on_delete=models.PROTECT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["first_name", "last_name", "birth_data"],
                                    name="unique_first_last_name_birth_data")
        ]
