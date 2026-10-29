from datetime import date

from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import OrderingFilter

from rest_framework.exceptions import ValidationError

from airport.models import (
    Airport,
    Route,
    AirplaneType,
    Airline,
    Airplane,
    SeatType,
    AirplaneSection,
    Flight,
    FlightStatus,
    CrewPosition,
    Crew,
)
from airport.serializers import (
    AirportSerializer,
    RouteSerializer,
    AirplaneTypeSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    SeatTypeSerializer,
    AirplaneSectionSerializer,
    FlightSerializer,
    CrewPositionSerializer,
    CrewSerializer,
)


class AirportViewSet(ModelViewSet):
    serializer_class = AirportSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["name", "code"]
    filter_fields = ["name", "code"]

    def get_filter_params(self):
        filter_params = {}

        for key in self.filter_fields:
            value = self.request.query_params.get(key, None)

            if value:
                filter_params[f"{key}__icontains"] = value

        return filter_params

    def get_queryset(self):

        return Airport.objects.filter(**self.get_filter_params())


class RouteViewSet(ModelViewSet):
    serializer_class = RouteSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["source__name", "destination__name"]
    filter_fields = ["source", "destination"]

    def get_filter_params(self):

        errors = {}
        filter_params = {}

        for key in self.filter_fields:
            value = self.request.query_params.get(key)
            if value:
                try:
                    filter_params[f"{key}"] = int(value)
                except ValueError:
                    errors[key] = "must be integer"
        if errors:
            raise ValidationError(errors)

        return filter_params

    def get_queryset(self):

        queryset = Route.objects.select_related("source", "destination")

        return queryset.filter(**self.get_filter_params())


class AirplaneTypeViewSet(ModelViewSet):
    serializer_class = AirplaneTypeSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["name"]

    def get_queryset(self):

        name = self.request.query_params.get("name", None)
        queryset = AirplaneType.objects.all()

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class AirlineViewSet(ModelViewSet):
    serializer_class = AirlineSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["name"]

    def get_queryset(self):

        name = self.request.query_params.get("name")
        queryset = Airline.objects.all()

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class AirplaneViewSet(ModelViewSet):
    serializer_class = AirplaneSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["name"]
    filter_fields = ["airplane_type", "airline", "name"]

    def get_filter_params(self):
        errors = {}
        filter_params = {}

        for key in self.filter_fields:
            value = self.request.query_params.get(key, None)

            if value:
                if key == "name":
                    filter_params[f"{key}__icontains"] = value
                    continue

                try:
                    filter_params[key] = int(value)
                except ValueError:
                    errors[key] = "must be integer"

        if errors:
            raise ValidationError(errors)

        return filter_params

    def get_queryset(self):

        queryset = Airplane.objects.select_related("airplane_type", "airline")

        filter_params = self.get_filter_params()

        return queryset.filter(**filter_params)


class SeatTypeViewSet(ModelViewSet):
    serializer_class = SeatTypeSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["name"]

    def get_queryset(self):

        name = self.request.query_params.get("name")
        queryset = SeatType.objects.all()

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class AirplaneSectionViewSet(ModelViewSet):
    serializer_class = AirplaneSectionSerializer

    def get_queryset(self):

        queryset = AirplaneSection.objects.select_related("airplane", "seat_type")

        airplane_id = self.request.query_params.get("airplane")

        if airplane_id:
            try:
                queryset = queryset.filter(airplane=int(airplane_id))
            except ValueError:
                raise ValidationError({"airplane": "must be integer"})

        return queryset


class FlightViewSet(ModelViewSet):
    serializer_class = FlightSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["departure_time", "arrival_time"]

    def get_filter_params(self) -> dict:
        query_params = self.request.query_params
        errors = {}
        filter_params = {}

        for param, lookup in (
            ("source", "route__source"),
            ("destination", "route__destination"),
        ):
            value = query_params.get(param)
            if value:
                try:
                    filter_params[lookup] = int(value)
                except ValueError:
                    errors[param] = "must be integer"

        for param, lookup in (
            ("departure", "departure_time__date"),
            ("arrival", "arrival_time__date"),
        ):
            value = query_params.get(param)
            if value:
                try:
                    filter_params[lookup] = date.fromisoformat(value)
                except ValueError:
                    errors[param] = "must be a date in format YYYY-MM-DD"

        flight_status = query_params.get("status")
        if flight_status:
            flight_status = flight_status.lower()
            if flight_status in FlightStatus.values:
                filter_params["status"] = flight_status
            else:
                errors["status"] = f"must be one of: {', '.join(FlightStatus.values)}"

        if errors:
            raise ValidationError(errors)

        return filter_params

    def get_queryset(self):
        queryset = Flight.objects.select_related("route", "airplane").prefetch_related(
            "crew"
        )

        filter_params = self.get_filter_params()

        return queryset.filter(**filter_params)


class CrewPositionViewSet(ModelViewSet):
    queryset = CrewPosition.objects.all()
    serializer_class = CrewPositionSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["name"]

    def get_queryset(self):

        name = self.request.query_params.get("name", None)
        queryset = CrewPosition.objects.all()

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class CrewViewSet(ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [OrderingFilter]
    ordering_fields = ["first_name", "last_name", "birth_date"]
    filter_fields = ["first_name", "last_name", "position"]

    def get_filter_params(self):
        filter_params = {}
        errors = {}
        for key in self.filter_fields:

            value = self.request.query_params.get(key)

            if value:
                if key != "position":
                    filter_params[f"{key}__icontains"] = value
                else:
                    try:
                        filter_params[f"{key}"] = int(value)
                    except ValueError:
                        errors[f"{key}"] = "must be integer"

        if errors:
            raise ValidationError(errors)

        return filter_params

    def get_queryset(self):
        queryset = Crew.objects.select_related("position")

        filter_params = self.get_filter_params()

        return queryset.filter(**filter_params)
