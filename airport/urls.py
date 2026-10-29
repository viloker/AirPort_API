from django.urls import include, path
from rest_framework.routers import DefaultRouter

from airport import views

router = DefaultRouter()
router.register("airports", views.AirportViewSet, basename="airport")
router.register("routes", views.RouteViewSet, basename="route")
router.register("airplane-types", views.AirplaneTypeViewSet, basename="airplanetype")
router.register("airlines", views.AirlineViewSet, basename="airline")
router.register("airplanes", views.AirplaneViewSet, basename="airplane")
router.register("seat-types", views.SeatTypeViewSet, basename="seattype")
router.register("airplane-sections", views.AirplaneSectionViewSet, basename="airplanesection")
router.register("flights", views.FlightViewSet, basename="flight")
router.register("crew-positions", views.CrewPositionViewSet)
router.register("crew", views.CrewViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "airport"