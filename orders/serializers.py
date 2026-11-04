from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import serializers

from airport.models import FlightStatus
from orders.models import PromoCode, Passenger, Ticket, Order

BOOKABLE_FLIGHT_STATUSES = (FlightStatus.SCHEDULED, FlightStatus.DELAYED)


class PromoCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PromoCode
        fields = [
            "id",
            "code",
            "discount_percent",
            "valid_from",
            "valid_to",
            "is_active",
        ]
        read_only_fields = ["id", "is_active"]

    def validate(self, attrs):

        valid_from = attrs.get("valid_from", getattr(self.instance, "valid_from", None))
        valid_to = attrs.get("valid_to", getattr(self.instance, "valid_to", None))

        if valid_from and valid_to and valid_from > valid_to:
            raise serializers.ValidationError(
                {"valid_to": "valid_to cannot be earlier than valid_from"}
            )
        return attrs


class PassengerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Passenger
        fields = ["id", "first_name", "last_name"]


class TicketCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ["flight", "row", "seat", "passenger"]

        validators = []

    def validate_passenger(self, passenger):
        user = self.context["request"].user
        if passenger.user_id != user.id:
            raise serializers.ValidationError("Passenger not found")
        return passenger

    def validate(self, attrs):
        flight = attrs["flight"]
        row = attrs["row"]
        seat = attrs["seat"]
        airplane = flight.airplane

        if flight.status not in BOOKABLE_FLIGHT_STATUSES:
            raise serializers.ValidationError(
                {"flight": f"Flight is {flight.status}, tickets can't be booked"}
            )
        if flight.departure_time <= timezone.now():
            raise serializers.ValidationError({"flight": "Flight has already departed"})

        if not 1 <= row <= airplane.rows:
            raise serializers.ValidationError(
                {"row": f"Row must be between 1 and {airplane.rows}"}
            )
        if not 1 <= seat <= airplane.seat_in_row:
            raise serializers.ValidationError(
                {"seat": f"Seat must be between 1 and {airplane.seat_in_row}"}
            )

        if Ticket.objects.filter(flight=flight, row=row, seat=seat).exists():
            raise serializers.ValidationError(
                {"seat": f"Seat {row}-{seat} is already taken"}
            )

        section = (
            airplane.sections.filter(row_from__lte=row, row_to__gte=row)
            .select_related("seat_type")
            .first()
        )
        if section is None or section.seat_type is None:
            raise serializers.ValidationError(
                {"row": f"Row {row} has no seat class in this airplane"}
            )

        attrs["seat_class"] = section.seat_type.name
        attrs["price"] = flight.price

        return attrs


class TicketListSerializer(serializers.ModelSerializer):

    source = serializers.CharField(source="flight.route.source.name", read_only=True)
    destination = serializers.CharField(
        source="flight.route.destination.name", read_only=True
    )
    departure_time = serializers.DateTimeField(
        source="flight.departure_time", read_only=True
    )
    arrival_time = serializers.DateTimeField(
        source="flight.arrival_time", read_only=True
    )
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "source",
            "destination",
            "departure_time",
            "arrival_time",
            "duration",
        ]

    def get_duration(self, ticket) -> int:
        delta = ticket.flight.arrival_time - ticket.flight.departure_time
        return int(delta.total_seconds() // 60)


class TicketDetailSerializer(TicketListSerializer):

    passenger = serializers.StringRelatedField()
    flight_status = serializers.CharField(source="flight.status", read_only=True)

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + [
            "flight",
            "flight_status",
            "passenger",
            "row",
            "seat",
            "seat_class",
            "price",
        ]


class OrderListSerializer(serializers.ModelSerializer):

    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "created_at", "total_price", "tickets"]


class OrderDetailSerializer(OrderListSerializer):

    promo_code = serializers.SlugRelatedField(slug_field="code", read_only=True)
    tickets = TicketDetailSerializer(many=True, read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + ["promo_code"]


class OrderCreateSerializer(serializers.ModelSerializer):

    promo_code = serializers.SlugRelatedField(
        slug_field="code",
        queryset=PromoCode.objects.all(),
        required=False,
        allow_null=True,
    )
    tickets = TicketCreateSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ["promo_code", "tickets"]

    def validate_promo_code(self, promo_code):
        if promo_code is not None and not promo_code.is_active:
            raise serializers.ValidationError("Promo code is not active")
        return promo_code

    def validate_tickets(self, tickets):
        seats = [(t["flight"].id, t["row"], t["seat"]) for t in tickets]
        if len(seats) != len(set(seats)):
            raise serializers.ValidationError("The same seat is booked twice")
        return tickets

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")

        try:
            with transaction.atomic():
                order = Order.objects.create(**validated_data)
                for ticket_data in tickets_data:
                    Ticket.objects.create(order=order, **ticket_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"tickets": "One of the seats was just taken, please try again"}
            )

        return order

    def to_representation(self, instance):
        return OrderDetailSerializer(instance, context=self.context).data
