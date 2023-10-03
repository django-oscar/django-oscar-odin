from django.test import TestCase
from oscar.core.loading import get_model

from oscar_odin.mappings import category

Product = get_model("catalogue", "Product")


class TestProduct(TestCase):
    fixtures = ["oscar_odin/catalogue"]

    def test_mapping__basic_model_to_resource(self):
        product = Product.objects.first()

        actual = category.product_to_resource(product)

        self.assertEqual(product.title, actual.title)

    def test_mapping__basic_product_with_out_of_stock_children(self):
        product = Product.objects.get(id=1)

        actual = category.product_to_resource(product)

        self.assertEqual(product.title, actual.title)

    def test_mapping__where_is_a_parent_product_do_not_include_children(self):
        product = Product.objects.get(id=8)

        actual = category.product_to_resource(product)

        self.assertEqual(product.title, actual.title)
        self.assertIsNone(actual.children)

    def test_mapping__where_is_a_parent_product_include_children(self):
        product = Product.objects.get(id=8)

        actual = category.product_to_resource(product, include_children=True)

        self.assertEqual(product.title, actual.title)
        self.assertIsNotNone(actual.children)
        self.assertEqual(3, len(actual.children))
