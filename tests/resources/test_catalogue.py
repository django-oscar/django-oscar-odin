from django.test import TestCase

from oscar_odin import resources


class TestProduct(TestCase):
    def test_init(self):
        target = resources.catalogue.Product()

        self.assertIsNotNone(target)
