import io
import PIL

from decimal import Decimal as D

from django.core.files import File
from django.test import TestCase

from oscar.core.loading import get_model

from oscar_odin.mappings.catalogue import products_to_db
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Image as ImageResource,
    ProductClass as ProductClassResource,
    Category as CategoryResource,
    ProductAttributeValue as ProductAttributeValueResource,
    ParentProduct as ParentProductResource,
)
from oscar_odin.exceptions import OscarOdinException
from oscar_odin.mappings.constants import (
    STOCKRECORD_PRICE,
    STOCKRECORD_NUM_IN_STOCK,
    STOCKRECORD_NUM_ALLOCATED,
    PRODUCTIMAGE_ORIGINAL,
)

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductImage = get_model("catalogue", "ProductImage")
Category = get_model("catalogue", "Category")
Partner = get_model("partner", "Partner")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class SingleProductReverseTest(TestCase):
    @property
    def image(self):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")
        return output

    def test_create_product_with_related_fields(self):
        product_class = ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        ProductAttribute.objects.create(
            name="Henk",
            code="henk",
            type=ProductAttribute.TEXT,
            product_class=product_class,
        )
        ProductAttribute.objects.create(
            name="Harrie",
            code="harrie",
            type=ProductAttribute.INTEGER,
            product_class=product_class,
        )

        product_class = ProductClassResource(slug="klaas", name="Klaas")

        partner = Partner.objects.create(name="klaas")

        Category.add_root(name="Hatsie", slug="batsie", is_public=True, code="1")
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")

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
                ImageResource(
                    caption="gekke caption",
                    display_order=0,
                    original=File(self.image, name="harrie.jpg"),
                ),
                ImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        prd = products_to_db(product_resource)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.title, "asdf2")
        self.assertEquals(prd.images.count(), 2)
        self.assertEquals(Category.objects.count(), 2)
        self.assertEquals(prd.categories.count(), 1)

        self.assertEquals(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEquals(stockrecord.price, D("20"))
        self.assertEquals(stockrecord.num_in_stock, 2)

        self.assertEquals(prd.attr.henk, "Klaas")
        self.assertEquals(prd.attr.harrie, 1)

        self.assertEquals(prd.images.count(), 2)

        product_resource = ProductResource(
            upc="1234323-2",
            price=D("21.50"),
            availability=3,
            currency="EUR",
            partner=partner,
            product_class=product_class,
            images=[
                ImageResource(
                    caption="gekke caption",
                    display_order=0,
                    original=File(self.image, name="harriebatsie.jpg"),
                ),
                ImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    original=File(self.image, name="vatsie.jpg"),
                ),
            ],
            categories=[CategoryResource(code="1")],
        )

        fields_to_update = [
            STOCKRECORD_PRICE,
            STOCKRECORD_NUM_IN_STOCK,
            STOCKRECORD_NUM_ALLOCATED,
            PRODUCTIMAGE_ORIGINAL,
        ]
        products_to_db(product_resource, fields_to_update=fields_to_update)

        prd = Product.objects.get(upc="1234323-2")
        self.assertEquals(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEquals(stockrecord.price, D("21.50"))
        self.assertEquals(stockrecord.num_in_stock, 3)
        self.assertEquals(prd.categories.count(), 2)

        self.assertEquals(prd.images.count(), 4)

    def test_idempotent(self):
        product_class = ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        ProductAttribute.objects.create(
            name="Henk",
            code="henk",
            type=ProductAttribute.TEXT,
            product_class=product_class,
        )
        ProductAttribute.objects.create(
            name="Harrie",
            code="harrie",
            type=ProductAttribute.INTEGER,
            product_class=product_class,
        )

        product_class = ProductClassResource(slug="klaas", name="Klaas")

        partner = Partner.objects.create(name="klaas")

        Category.add_root(name="Hatsie", slug="batsie", is_public=True, code="1")
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")

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
                ImageResource(
                    caption="gekke caption",
                    display_order=0,
                    original=File(self.image, name="harrie.jpg"),
                    code="12",
                ),
                ImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    original=File(self.image, name="vats.jpg"),
                    code="13",
                ),
            ],
            categories=[CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        prd = products_to_db(product_resource)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.title, "asdf2")
        self.assertEquals(prd.images.count(), 2)
        self.assertEquals(Category.objects.count(), 2)
        self.assertEquals(prd.categories.count(), 1)

        self.assertEquals(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEquals(stockrecord.price, D("20"))
        self.assertEquals(stockrecord.num_in_stock, 2)

        self.assertEquals(prd.attr.henk, "Klaas")
        self.assertEquals(prd.attr.harrie, 1)

        self.assertEquals(prd.images.count(), 2)

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
                ImageResource(
                    caption="gekke caption",
                    display_order=0,
                    original=File(self.image, name="harrie.jpg"),
                    code="12",
                ),
                ImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    original=File(self.image, name="vats.jpg"),
                    code="13",
                ),
            ],
            categories=[CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        products_to_db(product_resource)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.title, "asdf2")
        self.assertEquals(prd.images.count(), 2)
        self.assertEquals(Category.objects.count(), 2)
        self.assertEquals(prd.categories.count(), 1)

        self.assertEquals(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEquals(stockrecord.price, D("20"))
        self.assertEquals(stockrecord.num_in_stock, 2)

        self.assertEquals(prd.attr.henk, "Klaas")
        self.assertEquals(prd.attr.harrie, 1)

        self.assertEquals(prd.images.count(), 2)


class MultipleProductReverseTest(TestCase):
    @property
    def image(self):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")
        return output

    def test_create_simple_product(self):
        product_class = ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        Product.objects.create(upc="1234323asd", title="")
        product_class = ProductClassResource(slug="klaas", name="Klaas")

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
            ),
        ]

        prd = products_to_db(product_resources)

        self.assertEqual(Product.objects.count(), 2)

    def test_create_product_with_related_fields(self):
        product_class = ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        ProductAttribute.objects.create(
            name="Henk",
            code="henk",
            type=ProductAttribute.TEXT,
            product_class=product_class,
        )
        ProductAttribute.objects.create(
            name="Harrie",
            code="harrie",
            type=ProductAttribute.INTEGER,
            product_class=product_class,
        )

        product_class = ProductClassResource(slug="klaas", name="Klaas")

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
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        original=File(self.image, name="klaas.jpg"),
                    ),
                    ImageResource(
                        caption="gekke caption 2",
                        display_order=1,
                        original=File(self.image, name="harrie.jpg"),
                    ),
                ],
                attributes={"henk": "Poep", "harrie": 22},
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
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        original=File(self.image, name="klaas.jpg"),
                    ),
                    ImageResource(
                        caption="gekke caption 2",
                        display_order=1,
                        original=File(self.image, name="harrie.jpg"),
                    ),
                ],
                attributes={"henk": "Klaas", "harrie": 1},
            ),
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


class ParentChildTest(TestCase):
    def test_parent_childs(self):
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")
        ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        product_class = ProductClassResource(slug="klaas")
        partner = Partner.objects.create(name="klaas")

        prds = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.PARENT,
            product_class=product_class,
            categories=[CategoryResource(code="2")],
        )

        products_to_db(prds)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.structure, Product.PARENT)
        self.assertEquals(prd.product_class.slug, "klaas")

        child_product = ProductResource(
            parent=ParentProductResource(upc="1234323-2"),
            upc="1234323-child",
            title="asdf2 child",
            slug="asdf-asdfasdf2-child",
            structure=Product.CHILD,
            price=D("20"),
            availability=2,
            currency="EUR",
            partner=Partner.objects.create(name="klaas"),
        )

        products_to_db(child_product)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.structure, Product.PARENT)
        self.assertEquals(prd.product_class.slug, "klaas")

        child = Product.objects.get(upc="1234323-child")

        self.assertEquals(child.structure, Product.CHILD)
        self.assertEquals(child.parent.pk, prd.pk)

    def test_non_existing_parent_childs(self):
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")
        ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        product_class = ProductClassResource(slug="klaas")
        partner = Partner.objects.create(name="klaas")

        prds = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.PARENT,
            product_class=product_class,
            categories=[CategoryResource(code="2")],
        )

        products_to_db(prds)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEquals(prd.structure, Product.PARENT)
        self.assertEquals(prd.product_class.slug, "klaas")

        child_product = ProductResource(
            parent=ParentProductResource(upc="1234323-654"),
            upc="1234323-child",
            title="asdf2 child",
            slug="asdf-asdfasdf2-child",
            structure=Product.CHILD,
            price=D("20"),
            availability=2,
            currency="EUR",
            partner=Partner.objects.create(name="klaas"),
        )

        with self.assertRaises(OscarOdinException):
            products_to_db(child_product)
