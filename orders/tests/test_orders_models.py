from datetime import date, timedelta


from django.test import TestCase

from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

from orders.models import PromoCode, Passenger, Ticket, Order


class PromoCodeTest(TestCase):

    def test_code_is_unique(self):
        code = "test_code"
        PromoCode.objects.create(
            code=code,
            discount_percent=50,
            valid_from=date(2024, 1, 1),
            valid_to=date(2025, 12, 12),
        )
        with self.assertRaises(IntegrityError):
            PromoCode.objects.create(
                code=code,
                discount_percent=50,
                valid_from=date(2024, 1, 1),
                valid_to=date(2025, 12, 12),
            )

    def test_valid_from_can_not_be_more_than_valid_to(self):
        with self.assertRaises(ValidationError):
            PromoCode.objects.create(
                code="test_code",
                discount_percent=50,
                valid_from=date(2024, 1, 1),
                valid_to=date(2023, 12, 31),
            )

    def test_discount_percent_max_value_100(self):
        with self.assertRaises(ValidationError):
            PromoCode.objects.create(
                code="test_code",
                discount_percent=200,
                valid_from=date(2024, 1, 1),
                valid_to=date(2025, 1, 1),
            )

    def test_discount_percent_min_value_1(self):
        with self.assertRaises(ValidationError):
            PromoCode.objects.create(
                code="test_code",
                discount_percent=0,
                valid_from=date(2024, 1, 1),
                valid_to=date(2025, 1, 1),
            )

    def test_is_active_true(self):

        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date.today() - timedelta(days=1),
            valid_to=date.today() + timedelta(days=1),
        )

        self.assertTrue(promo_code.is_active)

    def test_is_active_false(self):

        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date(2024, 1, 1),
            valid_to=date(2025, 5, 5),
        )

        self.assertFalse(promo_code.is_active)

    def test_code_valid_only_one_day(self):
        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date.today(),
            valid_to=date.today()
        )

        self.assertTrue(promo_code.is_active)

    def test_valid_from_in_future(self):
        promo_code = PromoCode.objects.create(
            code="test_code",
            discount_percent=50,
            valid_from=date.today() + timedelta(days=1),
            valid_to=date.today() + timedelta(days=10)
        )

        self.assertFalse(promo_code.is_active)
        