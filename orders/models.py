from datetime import date

from django.db import models

from django.core.validators import MaxValueValidator
from django.contrib.auth import get_user_model

from airport.models import Flight


class PromoCode(models.Model):
    code = models.CharField(max_length=16, unique=True)
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(100)]
    )
    valid_from = models.DateField(default=date.today, blank=True)
    valid_to = models.DateField()

    @property
    def is_active(self):
        if self.valid_from <= date.today() <= self.valid_to:
            return True
        return False

    def __str__(self):
        return f"code: {self.code}, discount: {self.discount_percent}"


class Passenger(models.Model):
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)

    user = models.ForeignKey(
        get_user_model(), related_name="passengers", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Ticket(models.Model):
    flight = models.ForeignKey(Flight, related_name="tickets", on_delete=models.CASCADE)

    row = models.PositiveSmallIntegerField()
    seat = models.PositiveSmallIntegerField()

    seat_class = models.CharField(max_length=16)

    price = models.DecimalField(max_digits=7, decimal_places=2)

    order = models.ForeignKey("Order", related_name="tickets", on_delete=models.CASCADE)

    passenger = models.ForeignKey(
        Passenger, related_name="tickets", on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.flight}. Row: {self.row}, seat: {self.seat}, price: {self.price}"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    CANCELLED = "cancelled", "Cancelled"


class Order(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="orders", on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    promo_code = models.ForeignKey(
        PromoCode,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=12, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )

    total_paid = models.DecimalField(
        null=True, blank=True, editable=False, max_digits=10, decimal_places=2
    )

    @property
    def total_price(self):
        if self.status == OrderStatus.PAID:
            return self.total_paid

        discount = 0

        total = self.tickets.aggregate(price_sum=models.Sum("price", default=0)).get(
            "price_sum"
        )

        if self.promo_code is not None and self.promo_code.is_active:
            discount = total / 100 * self.promo_code.discount_percent

        return total - discount

    def __str__(self):
        return f"email: {self.user.email}, total_paid: {self.total_paid}"
