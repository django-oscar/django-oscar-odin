from django.test import TestCase

from oscar_odin import resources


class TestProduct(TestCase):
    def setUp(self):
        pass

    def test_init(self):
        resources.category.Product()
