from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

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
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class AirplaneTypeViewSet(ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirlineViewSet(ModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer


class AirplaneViewSet(ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer


class SeatTypeViewSet(ModelViewSet):
    queryset = SeatType.objects.all()
    serializer_class = SeatTypeSerializer


class AirplaneSectionViewSet(ModelViewSet):
    queryset = AirplaneSection.objects.all()
    serializer_class = AirplaneSectionSerializer


class FlightViewSet(ModelViewSet):
    queryset = Flight.objects.prefetch_related("crew")
    serializer_class = FlightSerializer


class CrewPositionViewSet(ModelViewSet):
    queryset = CrewPosition.objects.all()
    serializer_class = CrewPositionSerializer