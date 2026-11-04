from django.db.models import Prefetch

from rest_framework import mixins
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from orders.models import PromoCode, Passenger, Ticket, Order
from orders.serializers import (
    PromoCodeSerializer,
    PassengerSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
)


class PromoCodeViewSet(ModelViewSet):

    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAdminUser]


class PassengerViewSet(ModelViewSet):

    queryset = Passenger.objects.all()
    serializer_class = PassengerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Passenger.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):

    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tickets = Ticket.objects.select_related(
            "flight__route__source",
            "flight__route__destination",
            "passenger",
        )

        queryset = Order.objects.select_related("promo_code").prefetch_related(
            Prefetch("tickets", queryset=tickets)
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
