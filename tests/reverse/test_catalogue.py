import io
import PIL

from decimal import Decimal as D

from django.core.files import File
from django.test import TestCase

from oscar.core.loading import get_model

from oscar_odin.mappings.helpers import products_to_db
from oscar_odin.resources.catalogue import (
    ProductResource,
    ProductImageResource,
    ProductClassResource,
    CategoryResource,
    ParentProductResource,
    ProductRecommentationResource,
)
from oscar_odin.resources.partner import StockRecordResource, PartnerResource
from oscar_odin.exceptions import OscarOdinException
from oscar_odin.mappings.constants import (
    STOCKRECORD_PRICE,
    STOCKRECORD_NUM_IN_STOCK,
    STOCKRECORD_NUM_ALLOCATED,
    PRODUCTIMAGE_ORIGINAL,
    PRODUCT_TITLE,
    PRODUCT_UPC,
    PRODUCT_DESCRIPTION,
    PRODUCTCLASS_REQUIRESSHIPPING,
    MODEL_IDENTIFIERS_MAPPING,
)
from oscar_odin.mappings.partner import PartnerModelToResource

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductImage = get_model("catalogue", "ProductImage")
Category = get_model("catalogue", "Category")
Partner = get_model("partner", "Partner")
ProductRecommendation = get_model("catalogue", "ProductRecommendation")


class SingleProductReverseTest(TestCase):
    def setUp(self):
        super().setUp()
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

        Partner.objects.create(name="klaas")
        Category.add_root(name="Hatsie", slug="batsie", is_public=True, code="1")
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")

    @property
    def image(self):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")
        return output

    def test_create_product_with_related_fields(self):
        partner = Partner.objects.get(name="klaas")

        product_resource = ProductResource(
            upc="1234323-2",
            code="semek-mumtaz",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.STANDALONE,
            is_discountable=True,
            price=D("20"),
            availability=2,
            currency="EUR",
            partner=partner,
            product_class=ProductClassResource(slug="klaas"),
            images=[
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    code="harrie",
                    original=File(self.image, name="harrie.jpg"),
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.title, "asdf2")
        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(prd.categories.count(), 1)

        self.assertEqual(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEqual(stockrecord.price, D("20"))
        self.assertEqual(stockrecord.num_in_stock, 2)

        self.assertEqual(prd.attr.henk, "Klaas")
        self.assertEqual(prd.attr.harrie, 1)

        self.assertEqual(prd.images.count(), 2)

        product_resource = ProductResource(
            upc="1234323-2",
            code="haind-berrit",
            title="asdf2",
            structure=Product.STANDALONE,
            price=D("21.50"),
            availability=3,
            currency="EUR",
            partner=partner,
            product_class=ProductClassResource(slug="klaas"),
            images=[
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    code="harriebatsie",
                    original=File(self.image, name="harriebatsie.jpg"),
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vatsie",
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
        _, errors = products_to_db(product_resource, fields_to_update=fields_to_update)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")
        self.assertEqual(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEqual(stockrecord.price, D("21.50"))
        self.assertEqual(stockrecord.num_in_stock, 3)
        # Category was not included in fields_to_update
        self.assertEqual(prd.categories.count(), 1)
        self.assertFalse(prd.categories.filter(code="1").exists())

        self.assertEqual(prd.images.count(), 4)

    def test_create_productclass_with_product(self):
        partner = Partner.objects.get(name="klaas")
        product_class = ProductClassResource(slug="klaas", name="Klaas")

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
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    code="harrie",
                    original=File(self.image, name="harrie.jpg"),
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.product_class.slug, "klaas")

        self.assertEqual(prd.title, "asdf2")
        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(prd.categories.count(), 1)

        self.assertEqual(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEqual(stockrecord.price, D("20"))
        self.assertEqual(stockrecord.num_in_stock, 2)

        self.assertEqual(prd.images.count(), 2)

    def test_resource_default_value(self):
        product_class = ProductClassResource(slug="klaas", name="Klaas")
        product_resource = ProductResource(
            upc="1234",
            title="bat",
            slug="asdf",
            structure=Product.STANDALONE,
            product_class=product_class,
            is_discountable=False,
        )
        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)
        prd = Product.objects.get(upc="1234")
        self.assertEqual(prd.is_discountable, False)

        product_resource = ProductResource(
            upc="1234",
            title="bat",
            slug="asdf",
            structure=Product.STANDALONE,
            product_class=product_class,
        )
        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)
        prd.refresh_from_db()
        # Default value of is_discountable is considered from the ProductResource
        self.assertEqual(prd.is_discountable, True)

    def test_idempotent(self):
        partner = Partner.objects.get(name="klaas")
        product_class = ProductClassResource(slug="klaas", name="Klaas")

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
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    original=File(self.image, name="harrie.jpg"),
                    code="12",
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    original=File(self.image, name="vats.jpg"),
                    code="13",
                ),
            ],
            categories=[CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        identifier_mapping = MODEL_IDENTIFIERS_MAPPING.copy()
        # Test related fields in identifier mapping
        identifier_mapping[Product] = ("upc", "product_class.slug")
        _, errors = products_to_db(
            product_resource, identifier_mapping=identifier_mapping
        )
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.title, "asdf2")
        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(prd.categories.count(), 1)

        self.assertEqual(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEqual(stockrecord.price, D("20"))
        self.assertEqual(stockrecord.num_in_stock, 2)

        self.assertEqual(prd.attr.henk, "Klaas")
        self.assertEqual(prd.attr.harrie, 1)

        self.assertEqual(prd.images.count(), 2)

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.STANDALONE,
            # is_discountable=True,
            price=D("20"),
            availability=2,
            currency="EUR",
            partner=partner,
            product_class=product_class,
            images=[
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    original=File(self.image, name="harrie.jpg"),
                    code="12",
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    original=File(self.image, name="vats.jpg"),
                    code="13",
                ),
            ],
            categories=[CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.title, "asdf2")
        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(prd.categories.count(), 1)

        self.assertEqual(prd.stockrecords.count(), 1)
        stockrecord = prd.stockrecords.first()
        self.assertEqual(stockrecord.price, D("20"))
        self.assertEqual(stockrecord.num_in_stock, 2)

        self.assertEqual(prd.attr.henk, "Klaas")
        self.assertEqual(prd.attr.harrie, 1)

        self.assertEqual(prd.images.count(), 2)

    def test_create_product_with_multiple_stockrecords(self):
        partner = Partner.objects.get(name="klaas")

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.STANDALONE,
            is_discountable=True,
            stockrecords=[
                StockRecordResource(
                    partner=PartnerModelToResource.apply(partner),
                    partner_sku="123",
                    price=D("20"),
                    num_in_stock=2,
                    currency="EUR",
                ),
                StockRecordResource(
                    partner=PartnerModelToResource.apply(partner),
                    partner_sku="124",
                    price=D("30"),
                    num_in_stock=3,
                    currency="EUR",
                ),
            ],
            product_class=ProductClassResource(slug="klaas"),
            images=[
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    code="harrie",
                    original=File(self.image, name="harrie.jpg"),
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.stockrecords.count(), 2)
        stockrecord = prd.stockrecords.first()
        self.assertEqual(stockrecord.price, D("20"))
        self.assertEqual(stockrecord.num_in_stock, 2)
        stockrecord = prd.stockrecords.last()
        self.assertEqual(stockrecord.price, D("30"))
        self.assertEqual(stockrecord.num_in_stock, 3)


class MultipleProductReverseTest(TestCase):
    def setUp(self):
        super().setUp()
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

    @property
    def image(self):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")
        return output

    def test_create_simple_product(self):
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

        _, errors = products_to_db(product_resources)
        self.assertEqual(len(errors), 0)

        self.assertEqual(Product.objects.count(), 2)

    def test_creating_product_class_without_instance_full_clean(self):
        ProductClass.objects.all().delete()
        product_class = ProductClassResource(
            slug="klaas", name="Klaas", requires_shipping=True, track_stock=True
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
            ),
        ]

        _, errors = products_to_db(product_resources, clean_instances=False)
        self.assertEqual(len(errors), 0)
        self.assertEqual(Product.objects.count(), 2)

    def test_create_product_with_related_fields(self):
        partner = Partner.objects.create(name="klaas")

        product_resources = [
            ProductResource(
                upc="1234323",
                title="asdf1",
                partner=partner,
                slug="asdf-asdfasdf",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                price=D("20"),
                availability=2,
                currency="EUR",
                product_class=ProductClassResource(slug="klaas"),
                images=[
                    ProductImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="klaas",
                        original=File(self.image, name="klaas.jpg"),
                    ),
                    ProductImageResource(
                        caption="gekke caption 2",
                        display_order=1,
                        code="harrie",
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
                product_class=ProductClassResource(slug="klaas"),
                images=[
                    ProductImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="klass-2",
                        original=File(self.image, name="klaas.jpg"),
                    ),
                    ProductImageResource(
                        caption="gekke caption 2",
                        display_order=1,
                        code="harrie-2",
                        original=File(self.image, name="harrie.jpg"),
                    ),
                ],
                attributes={"henk": "Klaas", "harrie": 1},
            ),
        ]

        _, errors = products_to_db(product_resources)
        self.assertEqual(len(errors), 0)

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


class ProductRecommendationTest(TestCase):
    def setUp(self):
        super().setUp()
        ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        Partner.objects.create(name="klaas")

    def test_recommendation(self):
        product_resource = [
            ProductResource(
                upc="recommended_product1",
                title="asdf2",
                slug="asdf-asdfasdf2",
                description="description",
                structure=Product.STANDALONE,
                product_class=ProductClassResource(slug="klaas"),
            ),
            ProductResource(
                upc="recommended_product2",
                title="asdf2",
                slug="asdf-asdasdfasdf2",
                description="description",
                structure=Product.STANDALONE,
                product_class=ProductClassResource(slug="klaas"),
            ),
        ]

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        product_resource = ProductResource(
            upc="harses",
            title="asdf2",
            slug="asdf-asdfas23df2",
            description="description",
            structure=Product.STANDALONE,
            product_class=ProductClassResource(slug="klaas"),
            recommended_products=[
                ProductRecommentationResource(upc="recommended_product1"),
                ProductRecommentationResource(upc="recommended_product2"),
            ],
        )

        _, errors = products_to_db(product_resource, fields_to_update=[PRODUCT_UPC])
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="harses")

        self.assertEqual(ProductRecommendation.objects.count(), 2)
        self.assertEqual(prd.recommended_products.count(), 2)
        self.assertEqual(
            sorted(list(prd.recommended_products.values_list("upc", flat=True))),
            sorted(["recommended_product1", "recommended_product2"]),
        )

    def test_recommendation_non_existing(self):
        product_resource = [
            ProductResource(
                upc="recommended_product1",
                title="asdf2",
                slug="asdf-asdfasdf2",
                description="description",
                structure=Product.STANDALONE,
                product_class=ProductClassResource(slug="klaas"),
            ),
        ]

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        product_resource = ProductResource(
            upc="harses",
            title="asdf2",
            slug="asdf-asdfas23df2",
            description="description",
            structure=Product.STANDALONE,
            product_class=ProductClassResource(slug="klaas"),
            recommended_products=[
                ProductRecommentationResource(upc="recommended_product1"),
                ProductRecommentationResource(upc="recommended_product2"),
            ],
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            str(errors[0]),
            "Cannot create m2m relationship ProductRecommendation - related model 'Product' is missing a primary key",
        )


class ParentChildTest(TestCase):
    def setUp(self):
        super().setUp()
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")
        ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=True, track_stock=True
        )
        Partner.objects.create(name="klaas")

    def test_parent_childs(self):
        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.PARENT,
            product_class=ProductClassResource(slug="klaas"),
            categories=[CategoryResource(code="2")],
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.structure, Product.PARENT)
        self.assertEqual(prd.product_class.slug, "klaas")

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

        _, errors = products_to_db(child_product)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.structure, Product.PARENT)
        self.assertEqual(prd.product_class.slug, "klaas")

        child = Product.objects.get(upc="1234323-child")

        self.assertEqual(child.structure, Product.CHILD)
        self.assertEqual(child.parent.pk, prd.pk)

    def test_non_existing_parent_childs(self):
        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.PARENT,
            product_class=ProductClassResource(slug="klaas"),
            categories=[CategoryResource(code="2")],
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.structure, Product.PARENT)
        self.assertEqual(prd.product_class.slug, "klaas")

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


class SingleProductErrorHandlingTest(TestCase):
    def setUp(self):
        super().setUp()
        Partner.objects.create(name="klaas")
        Category.add_root(name="Hatsie", slug="batsie", is_public=True, code="1")
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")

    @property
    def image(self):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")
        return output

    def test_error_handling_on_product_operations(self):
        product_class = ProductClassResource(
            slug="klaas", name="Klaas", requires_shipping=True, track_stock=True
        )
        partner = Partner.objects.get(name="klaas")

        # Incorrect data for creating product
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
                ProductImageResource(
                    caption="gekke caption",
                    display_order="top",
                    code="harrie",
                    original=File(self.image, name="harrie.jpg"),
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
        )
        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].message_dict["images"][0]["0"]["display_order"][0],
            "'top' value must be a integer.",
        )

        # Correct Data for creating product
        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure=Product.STANDALONE,
            is_discountable=True,
            price="20",
            availability=2,
            currency="EUR",
            partner=partner,
            product_class=product_class,
            images=[
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    code="harrie",
                    original=File(self.image, name="harrie.jpg"),
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
        )
        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        # Incorrect data for updating product
        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="description",
            structure="new",
            is_discountable=53,
            price="expensive",
            availability=2,
            currency="EUR",
            partner=partner,
            product_class=product_class,
            images=[
                ProductImageResource(code="harrie"),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order="Alphabet",
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
        )
        _, errors = products_to_db(product_resource)

        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].message_dict["structure"][0],
            "Value 'new' is not a valid choice.",
        )
        self.assertEqual(
            errors[0].message_dict["is_discountable"][0],
            "'53' value must be either True or False.",
        )
        self.assertEqual(
            errors[0].message_dict["images"][0]["1"]["display_order"][0],
            "'Alphabet' value must be a integer.",
        )
        self.assertEqual(
            errors[0].message_dict["price"][0],
            "'expensive' value must be a decimal.",
        )


class ProductFieldsToUpdateTest(TestCase):
    def setUp(self):
        super().setUp()
        ProductClass.objects.create(
            name="Klaas", slug="klaas", requires_shipping=False, track_stock=True
        )
        Partner.objects.create(name="klaas")
        Category.add_root(name="Hatsie", slug="batsie", is_public=True, code="1")
        Category.add_root(name="henk", slug="klaas", is_public=True, code="2")

    @property
    def image(self):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")
        return output

    def test_fields_to_update_on_product_operations(self):
        product_class = ProductClassResource(slug="klaas")
        partner = Partner.objects.get(name="klaas")

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            description="old description",
            structure=Product.STANDALONE,
            price=D("20"),
            availability=2,
            currency="EUR",
            partner=partner,
            product_class=product_class,
            images=[
                ProductImageResource(
                    caption="gekke caption",
                    display_order=0,
                    code="harrie",
                    original=File(self.image, name="harrie.jpg"),
                ),
                ProductImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            categories=[CategoryResource(code="2")],
        )
        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            description="updated description",
            structure=Product.STANDALONE,
            product_class=product_class,
        )
        _, errors = products_to_db(product_resource)
        prd = Product.objects.get(upc="1234323-2")
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].message_dict["slug"][0],
            "This field cannot be null.",
        )
        self.assertEqual(prd.categories.count(), 1)
        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(prd.stockrecords.count(), 1)

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            description="This description is not updated",
            structure=Product.STANDALONE,
            product_class=product_class,
        )
        _, errors = products_to_db(product_resource, fields_to_update=[PRODUCT_TITLE])
        # Slug error doesn't appear because it is not included in fields_to_update
        self.assertEqual(len(errors), 0)
        prd.refresh_from_db()
        # Description is not updated it is not included in fields_to_update
        self.assertEqual(prd.description, "old description")

        product_resource = ProductResource(
            upc="1234323-2",
            title="target",
            description="This description is updated",
            structure=Product.STANDALONE,
            product_class=product_class,
        )
        _, errors = products_to_db(
            product_resource, fields_to_update=[PRODUCT_DESCRIPTION]
        )
        self.assertEqual(len(errors), 0)
        prd.refresh_from_db()
        # Description is not updated it is not included in fields_to_update
        self.assertEqual(prd.description, "This description is updated")
        # Likewise title is also not updated since we did not include
        # it in fields_to_update.
        self.assertNotEqual(prd.title, "target")

    def test_product_class_fields_to_update(self):
        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            structure=Product.STANDALONE,
        )
        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].message_dict["__all__"][0],
            "Your product must have a product class.",
        )

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            structure=Product.STANDALONE,
            product_class=ProductClassResource(
                name="Better", slug="better", requires_shipping=False, track_stock=True
            ),
        )
        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            structure=Product.STANDALONE,
        )
        _, errors = products_to_db(product_resource, fields_to_update=[PRODUCT_TITLE])
        # Update fails, removing product_class from product resource produces error
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].message_dict["__all__"][0],
            "Your product must have a product class.",
        )

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            structure=Product.STANDALONE,
            product_class=ProductClassResource(slug="better", requires_shipping=True),
        )
        _, errors = products_to_db(product_resource, fields_to_update=[PRODUCT_TITLE])
        self.assertEqual(len(errors), 0)
        prd = Product.objects.get(upc="1234323-2")
        # Product class is not updated since it wasn't added in fields_to_update
        self.assertNotEqual(prd.product_class.requires_shipping, True)

        _, errors = products_to_db(
            product_resource, fields_to_update=[PRODUCTCLASS_REQUIRESSHIPPING]
        )
        self.assertEqual(len(errors), 0)
        prd.refresh_from_db()
        # Product class is updated as it was added in fields_to_update
        self.assertEqual(prd.product_class.requires_shipping, True)

    def test_check_multiple_products_with_same_new_product_class(self):
        product_resources = [
            ProductResource(
                upc="checking",
                title="Checking",
                slug="checking",
                structure=Product.STANDALONE,
                product_class=ProductClassResource(
                    name="Better",
                    slug="better",
                    requires_shipping=False,
                    track_stock=True,
                ),
            ),
            ProductResource(
                upc="testing",
                title="Testing",
                slug="testing",
                structure=Product.STANDALONE,
                product_class=ProductClassResource(
                    name="Better",
                    slug="better",
                    requires_shipping=False,
                    track_stock=True,
                ),
            ),
        ]
        _, errors = products_to_db(product_resources)
        self.assertEqual(len(errors), 0)

    def test_product_import_with_non_existent_product_class(self):
        product_resources = [
            ProductResource(
                upc="checking",
                title="Checking",
                slug="checking",
                structure=Product.STANDALONE,
                product_class=ProductClassResource(
                    slug="better",
                ),
            ),
            ProductResource(
                upc="testing",
                title="Testing",
                slug="testing",
                structure=Product.STANDALONE,
                product_class=ProductClassResource(
                    name="Nice",
                    slug="nice",
                    requires_shipping=True,
                    track_stock=True,
                ),
            ),
        ]
        # i.e, ProductClass with slug="better" not found.
        with self.assertRaises(Exception):
            products_to_db(product_resources, clean_instances=True)
