from django.urls import include, path
from rest_framework.routers import DefaultRouter

from orders.views import PromoCodeViewSet, PassengerViewSet, OrderViewSet

router = DefaultRouter()
router.register("promo-codes", PromoCodeViewSet)
router.register("passengers", PassengerViewSet)
router.register("orders", OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "orders"
