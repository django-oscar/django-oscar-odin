from django.test import TestCase
from oscar.core.loading import get_model

from oscar_odin.mappings import order

Order = get_model("order", "Order")


class TestOrder(TestCase):
    fixtures = [
        "oscar_odin/auth",
        "oscar_odin/catalogue",
        "oscar_odin/partner",
        "oscar_odin/offer",
        "oscar_odin/address",
        "oscar_odin/order",
    ]

    def test_mapping__basic_model_to_resource(self):
        order_model = Order.objects.first()

        actual = order.order_to_resource(order_model)

        self.assertEqual(order_model.number, actual.number)
