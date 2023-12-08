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


class SingleProductReverseTest(TestCase):
    def test_create_product_with_related_fields(self):
        product_class = ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        ProductAttribute.objects.create(
            name="Henk", code="henk", type=ProductAttribute.TEXT, product_class=product_class
        )
        ProductAttribute.objects.create(
            name="Harrie", code="harrie", type=ProductAttribute.INTEGER, product_class=product_class
        )
        
        product_class = ProductClassResource(
            slug="klaas", name="Klaas"
        )
        
        partner = Partner.objects.create(name="klaas")

        Category.add_root(name="Hatsie", slug="batsie", is_public=True)
        Category.add_root(name="henk", slug="klaas", is_public=True)

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.STANDALONE,
            is_discountable=True,
            price=D("20"),
            availability=2,
            currency="EUR",
            partner=partner,
            product_class=product_class,
            images=[
                ImageResource(caption="gekke caption", display_order=0),
                ImageResource(caption="gekke caption 2", display_order=1),
            ],
            categories=[CategoryResource(name="henk", slug="klaas"), CategoryResource(name="Hatsie datsie", slug="batsie")],
            attributes={"henk": "Klaas", "harrie": 1}
        )

        prd = products_to_db(product_resource)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.title, "asdf2")
        self.assertEquals(Category.objects.get(slug="batsie").name, "Hatsie datsie")
        self.assertEquals(prd.images.count(), 2)
        self.assertEquals(Category.objects.count(), 2)
        self.assertEquals(prd.categories.count(), 2)
      
        self.assertEquals(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEquals(stockrecord.price, D("20"))
        self.assertEquals(stockrecord.num_in_stock, 2)

        self.assertEquals(prd.attr.henk, "Klaas")
        self.assertEquals(prd.attr.harrie, 1)
        
        product_resource = ProductResource(
            upc="1234323-2",
            price=D("21.50"),
            availability=3,
            currency="EUR",
            partner=partner,
            product_class=product_class,
            categories=[CategoryResource(name="henk", slug="klaas"), CategoryResource(name="Hatsie datsie", slug="batsie")],
        )
        
        fields_to_update = ["upc", "price", "num_in_stock", "num_allocated"]
        products_to_db(product_resource, fields_to_update=fields_to_update)

        prd = Product.objects.get(upc="1234323-2")
        self.assertEquals(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEquals(stockrecord.price, D("21.50"))
        self.assertEquals(stockrecord.num_in_stock, 3)
        self.assertEquals(prd.categories.count(), 2)


class MultipleProductReverseTest(TestCase):
    def test_create_simple_product(self):
        product_class = ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        Product.objects.create(upc="1234323asd", title="")
        product_class = ProductClassResource(
            slug="klaas", name="Klaas"
        )
        
        product_resources = [
            ProductResource(
                upc="1234323asd",
                title="asdf1",
                slug="asdf-asdfasdf",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                product_class=product_class,
            ),
            ProductResource(
                upc="1234323-2",
                title="asdf2",
                slug="asdf-asdfasdf-2",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                product_class=product_class,
            )
        ]

        prd = products_to_db(product_resources)

        self.assertEqual(Product.objects.count(), 2)

    def test_create_product_with_related_fields(self):
        product_class = ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        ProductAttribute.objects.create(
            name="Henk", code="henk", type=ProductAttribute.TEXT, product_class=product_class
        )
        ProductAttribute.objects.create(
            name="Harrie", code="harrie", type=ProductAttribute.INTEGER, product_class=product_class
        )
        
        product_class = ProductClassResource(
            slug="klaas", name="Klaas"
        )

        product_resources = [
            ProductResource(
                upc="1234323",
                title="asdf1",
                slug="asdf-asdfasdf",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                price=D("20"),
                availability=2,
                currency="EUR",
                product_class=product_class,
                images=[
                    ImageResource(caption="gekke caption", display_order=0),
                    ImageResource(caption="gekke caption 2", display_order=1),
                ],
                attributes={"henk": "Poep", "harrie": 22}
            ),
            ProductResource(
                upc="1234323-2",
                title="asdf2",
                slug="asdf-asdfasdf2",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                price=D("20"),
                availability=2,
                currency="EUR",
                partner=Partner.objects.create(name="klaas"),
                product_class=product_class,
                images=[
                    ImageResource(caption="gekke caption", display_order=0),
                    ImageResource(caption="gekke caption 2", display_order=1),
                ],
                attributes={"henk": "Klaas", "harrie": 1}
            )
        ]

        products_to_db(product_resources)

        self.assertEqual(ProductImage.objects.all().count(), 4)
        self.assertEqual(ProductClass.objects.all().count(), 1)
        self.assertEqual(Product.objects.all().count(), 2)

        prd = Product.objects.get(upc="1234323")
        prd2 = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(prd2.images.count(), 2)

        self.assertEqual(prd.attr.henk, "Poep")
        self.assertEqual(prd.attr.harrie, 22)

        self.assertEqual(prd2.attr.henk, "Klaas")
        self.assertEqual(prd2.attr.harrie, 1)

