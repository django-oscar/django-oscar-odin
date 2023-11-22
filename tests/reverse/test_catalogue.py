from django.test import TestCase
from oscar.core.loading import get_model

from oscar_odin.mappings.catalogue import product_to_db
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Image as ImageResource,
    ProductClass as ProductClassResource,
)

Product = get_model("catalogue", "Product")


class ProductReverseTest(TestCase):
    def test_create_simple_product(self):
        product_resource = ProductResource(
            upc="1234323",
            title="asdf1",
            slug="asdf-asdfasdf",
            description="description",
            structure=Product.STANDALONE,
            is_discountable=True,
            product_class=ProductClassResource(
                name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
            ),
        )

        prd = product_to_db(product_resource)

        prd = Product.objects.get(upc="1234323")
        
        self.assertEquals(prd.title, "asdf1")

    def test_create_product_with_related_fields(self):
        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.STANDALONE,
            is_discountable=True,
            product_class=ProductClassResource(
                name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
            ),
            images=[ImageResource(caption="gekke caption", display_order=0), ImageResource(caption="gekke caption 2", display_order=1)],
        )

        prd = product_to_db(product_resource)
        
        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.title, "asdf2")
        
        self.assertEquals(prd.images.count(), 2)
