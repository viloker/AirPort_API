from rest_framework.serializers import ModelSerializer

from airport.models import (
    Airport,
    Route,
    AirplaneType,
    Airline,
    Airplane,
    SeatType,
    AirplaneSection,
    Flight,
    CrewPosition,
    Crew,
)


class AirportSerializer(ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "code", "closest_big_city"]


class RouteSerializer(ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class AirplaneTypeSerializer(ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirlineSerializer(ModelSerializer):
    class Meta:
        model = Airline
        fields = ["id", "name"]


class AirplaneSerializer(ModelSerializer):
    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "rows",
            "seat_in_row",
            "total_seats",
            "airplane_type",
            "airline",
        ]


class SeatTypeSerializer(ModelSerializer):
    class Meta:
        model = SeatType
        fields = ["id", "name"]


class AirplaneSectionSerializer(ModelSerializer):
    class Meta:
        model = AirplaneSection
        fields = ["id", "airplane", "seat_type", "row_from", "row_to"]


class FlightSerializer(ModelSerializer):
    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "status",
            "crew",
        ]


class CrewPositionSerializer(ModelSerializer):
    class Meta:
        model = CrewPosition
        fields = ["id", "name"]


class CrewSerializer(ModelSerializer):
    class Meta:
        model = Crew
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "number_phone",
            "birth_date",
            "position",
        ]
