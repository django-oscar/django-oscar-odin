from django.test import TestCase
from oscar.core.loading import get_model

from oscar_odin.mappings.catalogue import products_to_db
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Image as ImageResource,
    ProductClass as ProductClassResource,
    Category as CategoryResource
)

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductImage = get_model("catalogue", "ProductImage")
Category = get_model("catalogue", "Category")


class SignleProductReverseTest(TestCase):
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

        prd = products_to_db(product_resource)

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
            images=[
                ImageResource(caption="gekke caption", display_order=0),
                ImageResource(caption="gekke caption 2", display_order=1),
            ],
            categories=[
                CategoryResource(name="klaas", slug="henk", is_public=True)
            ]
        )

        prd = products_to_db(product_resource)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.title, "asdf2")

        self.assertEquals(prd.images.count(), 2)
        self.assertEquals(Category.objects.count(), 1)
        self.assertEquals(prd.categories.count(), 1)


class MultipleProductReverseTest(TestCase):
    def test_create_simple_product(self):
        product_resources = [
            ProductResource(
                upc="1234323",
                title="asdf1",
                slug="asdf-asdfasdf",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                product_class=ProductClassResource(
                    name="Klaas",
                    slug="klaasas",
                    requires_shipping=True,
                    track_stock=True,
                ),
            ),
            ProductResource(
                upc="1234323-2",
                title="asdf2",
                slug="asdf-asdfgasfdg",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                product_class=ProductClassResource(
                    name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
                ),
            ),
        ]

        products = products_to_db(product_resources)

        self.assertEquals(Product.objects.all().count(), 2)
        self.assertEquals(ProductClass.objects.all().count(), 2)

    def test_create_product_with_related_fields(self):
        product_resources = [
            ProductResource(
                upc="1234323",
                title="asdf1",
                slug="asdf-asdfasdf",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                product_class=ProductClassResource(
                    name="Klaas",
                    slug="klaasas",
                    requires_shipping=True,
                    track_stock=True,
                ),
                images=[
                    ImageResource(caption="gekke caption", display_order=0),
                    ImageResource(caption="gekke caption 2", display_order=1),
                ],
            ),
            ProductResource(
                upc="1234323-2",
                title="asdf2",
                slug="asdf-asdfasdf2",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                product_class=ProductClassResource(
                    name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
                ),
                images=[
                    ImageResource(caption="gekke caption", display_order=0),
                    ImageResource(caption="gekke caption 2", display_order=1),
                ],
            ),
        ]
        
        products_to_db(product_resources)

        self.assertEqual(ProductImage.objects.all().count(), 4)
        self.assertEqual(ProductClass.objects.all().count(), 2)
        self.assertEqual(Product.objects.all().count(), 2)

        prd = Product.objects.get(upc="1234323")
        prd2 = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(prd2.images.count(), 2)
