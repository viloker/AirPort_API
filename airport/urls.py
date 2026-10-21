from django.urls import include, path
from rest_framework.routers import DefaultRouter

from airport import views

router = DefaultRouter()
router.register("airports", views.AirportViewSet)
router.register("routes", views.RouteViewSet)
router.register("airplane-types", views.AirplaneTypeViewSet)
router.register("airlines", views.AirlineViewSet)
router.register("airplanes", views.AirplaneViewSet)
router.register("seat-types", views.SeatTypeViewSet)
router.register("airplane-sections", views.AirplaneSectionViewSet)
router.register("flights", views.FlightViewSet)
router.register("crew-positions", views.CrewPositionViewSet)
router.register("crew", views.CrewViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "airport"