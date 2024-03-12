from decimal import Decimal
from django.test import TestCase
from oscar.core.loading import get_model

from oscar_odin.mappings import order

Order = get_model("order", "Order")
Discount = get_model("order", "orderdiscount")
Product = get_model("catalogue", "product")
Basket = get_model("basket", "Basket")


class TestDiscount(TestCase):
    fixtures = [
        "oscar_odin/test_discount/partner",
        "oscar_odin/test_discount/address",
        "oscar_odin/test_discount/auth",
        "oscar_odin/test_discount/order",
        "oscar_odin/test_discount/catalogue",
    ]

    def test_total_prices(self):
        order_obj = Order.objects.first()

        actual = order.order_to_resource(order_obj)

        self.assertEqual(order_obj.total_incl_tax, actual.total_incl_tax)
        self.assertEqual(order_obj.total_excl_tax, actual.total_excl_tax)

    def test_discount_lines_per_tax_code_length(self):
        order_obj = Order.objects.get(number=100022)

        actual = order.order_to_resource(order_obj)

        self.assertEqual(2, len(actual.discounts[0].discount_lines_per_tax_code))
        self.assertEqual(2, len(actual.discounts[1].discount_lines_per_tax_code))

    def test_discount_lines_per_tax_code_amounts(self):
        order_obj = Order.objects.get(number=100022)

        actual = order.order_to_resource(order_obj)

        self.assertEqual(
            Decimal("3.49"), actual.discounts[0].discount_lines_per_tax_code[0].amount
        )
        self.assertEqual(
            Decimal("1.49"), actual.discounts[0].discount_lines_per_tax_code[1].amount
        )
        self.assertEqual(
            Decimal("1.00"), actual.discounts[1].discount_lines_per_tax_code[0].amount
        )
        self.assertEqual(
            Decimal("1.00"), actual.discounts[1].discount_lines_per_tax_code[1].amount
        )

    def test_discount_lines_per_tax_code_without_discounts(self):
        order_obj = Order.objects.get(number=100023)

        actual = order.order_to_resource(order_obj)

        self.assertEqual([], actual.discounts)
