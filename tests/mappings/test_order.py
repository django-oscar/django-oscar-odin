from django.test import TestCase
from oscar.core.loading import get_model

Order = get_model("order", "Order")


class TestOrder(TestCase):
    pass
