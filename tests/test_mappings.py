from django.test import TestCase
from oscar.core.loading import get_model

from oscar_odin.mappings import ProductToResource

Product = get_model("catalogue", "Product")


class TestProduct(TestCase):
    fixtures = ["oscar_odin/catalogue"]

    def test_mapping__basic_model_to_resource(self):
        model_product = Product.objects.first()

        actual = ProductToResource.apply(model_product)

        self.assertEqual(model_product.title, actual.title)
