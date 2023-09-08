from django.test import TestCase

from oscar.core.loading import get_model

from oscar_odin import resources

Product = get_model("catalogue", "Product")


class TestProduct(TestCase):
    fixtures = ["oscar_odin/catalogue"]

    def test_init(self):
        model_product = Product.objects.first()
        self.assertNotEqual(model_product, None)

        resource_product = resources.category.Product()
        # ToDo: Make it so this assert passes
        self.assertEqual(model_product.title, resource_product.title)
