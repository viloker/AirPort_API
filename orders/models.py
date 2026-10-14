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

class Passenger(models.Model):
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)

    user = models.ForeignKey(get_user_model(), related_name="passengers", on_delete=models.CASCADE)


class Ticket(models.Model):
    flight = models.ForeignKey(Flight, related_name="tickets", on_delete=models.CASCADE)

    row = models.PositiveSmallIntegerField()
    seat = models.PositiveSmallIntegerField()

    seat_class = models.CharField(max_length=16)

    price = models.DecimalField(max_digits=7, decimal_places=2)

    order = models.ForeignKey("Order", related_name="tickets", on_delete=models.PROTECT)

    passenger = models.ForeignKey(Passenger, related_name="tickets", on_delete=models.PROTECT)



class Order(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="orders", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    promo_code = models.ForeignKey(
        PromoCode,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    @property
    def total_price(self):

        price = sum(list(self.tickets.all().values_list("price")))
        sale = 0
        if self.promo_code.is_active:
            sale = price / 100 * self.promo_code.discount_percent

        return price - sale
        