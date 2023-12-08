from django.test import TestCase

from oscar_odin import resources

from decimal import Decimal as D

from django.test import TestCase
from oscar.core.loading import get_model

from oscar_odin.mappings.catalogue import products_to_db
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Image as ImageResource,
    ProductClass as ProductClassResource,
    Category as CategoryResource,
    ProductAttributeValue as ProductAttributeValueResource
)

from oscar_odin.mappings.defaults import DEFAULT_UPDATE_FIELDS

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductImage = get_model("catalogue", "ProductImage")
Category = get_model("catalogue", "Category")
Partner = get_model("partner", "Partner")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class TestProduct(TestCase):
    def test_init(self):
        target = resources.catalogue.Product()

        self.assertIsNotNone(target)
