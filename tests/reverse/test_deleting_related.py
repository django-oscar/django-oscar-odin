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
    ProductRecommentation as ProductRecommentationResource,
)
from oscar_odin.mappings.constants import (
    CATEGORY_CODE,
    ALL_PRODUCTIMAGE_FIELDS,
    ALL_STOCKRECORD_FIELDS,
)

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
Category = get_model("catalogue", "Category")
ProductImage = get_model("catalogue", "ProductImage")
Partner = get_model("partner", "Partner")
Stockrecord = get_model("partner", "Stockrecord")
ProductCategory = get_model("catalogue", "ProductCategory")


class DeleteRelatedModelReverseTest(TestCase):
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

    def test_deleting_product_related_models(self):
        partner = Partner.objects.get(name="klaas")
        # If an attribute is present in product class and not included in the product
        # resource, oscar's ProductAttributeContainer would require product class name
        # in the __str__ method. Hence its important to include name in the following
        # product class resource. This is not needed for oscar version greater than
        # 3.2.4.
        product_class = ProductClassResource(slug="klaas", name="Klaas")

        product_resources = [
            ProductResource(
                upc="1234323-2",
                title="asdf2",
                slug="asdf-asdfasdf2",
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                price=D("10"),
                availability=2,
                currency="EUR",
                partner=partner,
                product_class=product_class,
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="harrie",
                        original=File(self.image, name="harrie.jpg"),
                    ),
                    ImageResource(
                        caption="gekke caption 2",
                        display_order=1,
                        code="vats",
                        original=File(self.image, name="vats.jpg"),
                    ),
                ],
                categories=[CategoryResource(code="1"), CategoryResource(code="2")],
                attributes={"henk": "Klaas", "harrie": 1},
            ),
            ProductResource(
                upc="563-2",
                title="bat",
                slug="bat",
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
                        caption="robin",
                        display_order=0,
                        code="robin",
                        original=File(self.image, name="robin.jpg"),
                    ),
                ],
                categories=[CategoryResource(code="1")],
                attributes={"henk": "Klaas"},
            ),
        ]

        self.assertEqual(Stockrecord.objects.count(), 0)
        _, errors = products_to_db(product_resources)
        self.assertEqual(Stockrecord.objects.count(), 2)
        self.assertEqual(len(errors), 0)
        prd = Product.objects.get(upc="1234323-2")
        prd_563 = Product.objects.get(upc="563-2")

        self.assertEqual(prd.images.count(), 2)
        self.assertTrue(prd.images.filter(code="harrie").exists())
        self.assertTrue(prd.images.filter(code="vats").exists())

        self.assertEqual(prd.stockrecords.count(), 1)
        self.assertTrue(prd.stockrecords.filter(partner=partner).exists())
        self.assertEqual(prd.stockrecords.first().price, D("10"))
        self.assertEqual(prd_563.stockrecords.count(), 1)
        self.assertTrue(prd_563.stockrecords.filter(partner=partner).exists())
        self.assertEqual(prd_563.stockrecords.first().price, D("20"))

        self.assertEqual(prd.categories.count(), 2)
        self.assertTrue(prd.categories.filter(code="1").exists())
        self.assertTrue(prd.categories.filter(code="2").exists())
        self.assertEqual(prd_563.categories.count(), 1)
        self.assertTrue(prd_563.categories.filter(code="1").exists())

        self.assertEqual(prd.attribute_values.count(), 2)
        self.assertEqual(prd.attr.henk, "Klaas")
        self.assertEqual(prd.attr.harrie, 1)

        # Manually add another stockrecord in product and check if its deleted later
        partner_henk = Partner.objects.create(name="henry")
        Stockrecord.objects.create(
            partner=partner_henk, product=prd, num_in_stock=4, price=D("20.0")
        )
        self.assertEqual(prd.stockrecords.count(), 2)
        self.assertTrue(prd.stockrecords.filter(partner=partner).exists())
        self.assertTrue(prd.stockrecords.filter(partner=partner_henk).exists())

        product_resources = [
            ProductResource(
                upc="1234323-2",
                title="asdf2",
                structure=Product.STANDALONE,
                price=D("20"),
                availability=2,
                currency="EUR",
                partner=partner,
                product_class=product_class,
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="harrie",
                        original=File(self.image, name="harrie.jpg"),
                    ),
                ],
                attributes={"henk": "Klaas", "harrie": None},
            ),
            ProductResource(
                upc="563-2",
                title="bat",
                structure=Product.STANDALONE,
                price=D("20"),
                availability=2,
                currency="EUR",
                partner=partner,
                product_class=product_class,
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="harrie",
                        original=File(self.image, name="harrie.jpg"),
                    ),
                ],
                categories=[CategoryResource(code="1"), CategoryResource(code="2")],
                attributes={"henk": "Klaas", "harrie": None},
            ),
        ]

        fields_to_update = ALL_PRODUCTIMAGE_FIELDS + ALL_STOCKRECORD_FIELDS
        _, errors = products_to_db(
            product_resources, delete_related=True, fields_to_update=fields_to_update
        )
        self.assertEqual(len(errors), 0)

        # Related models are successfully deleted
        self.assertEqual(prd.images.count(), 1)
        self.assertTrue(prd.images.filter(code="harrie").exists())

        self.assertEqual(prd.stockrecords.count(), 1)
        self.assertTrue(prd.stockrecords.filter(partner=partner).exists())

        self.assertEqual(prd.attribute_values.count(), 1)
        self.assertEqual(prd.attr.henk, "Klaas")

        # Since categories were added in the fields_to_update attribute,
        # so they remain unaffected
        self.assertEqual(prd.categories.count(), 2)
        self.assertTrue(prd.categories.filter(code="1").exists())
        self.assertTrue(prd.categories.filter(code="2").exists())
        # Likewise, the new category added in product 563-2 was not updated
        self.assertEqual(prd_563.categories.count(), 1)
        self.assertTrue(prd_563.categories.filter(code="1").exists())

        # Adding categories and deleting one
        product_resources = [
            ProductResource(
                upc="1234323-2",
                title="asdf2",
                structure=Product.STANDALONE,
                categories=[CategoryResource(code="1")],
            ),
            ProductResource(
                upc="563-2", title="bat", structure=Product.STANDALONE, categories=[]
            ),
        ]
        _, errors = products_to_db(
            product_resources, delete_related=True, fields_to_update=[CATEGORY_CODE]
        )
        self.assertEqual(len(errors), 0)
        # Categories of prd_563 are deleted since it is set to an empty array
        self.assertEqual(prd_563.categories.count(), 0)
        self.assertEqual(prd.categories.count(), 1)
        self.assertTrue(prd.categories.filter(code="1").exists())
        self.assertEqual(prd.images.count(), 1)
        self.assertEqual(prd.stockrecords.count(), 1)
        self.assertEqual(prd.attribute_values.count(), 1)

    def test_deleting_all_related_models(self):
        partner = Partner.objects.get(name="klaas")

        Product.objects.create(upc="recommended_product1")

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
            product_class=ProductClassResource(slug="klaas"),
            images=[
                ImageResource(
                    caption="gekke caption",
                    display_order=0,
                    code="harrie",
                    original=File(self.image, name="harrie.jpg"),
                ),
                ImageResource(
                    caption="gekke caption 2",
                    display_order=1,
                    code="vats",
                    original=File(self.image, name="vats.jpg"),
                ),
            ],
            recommended_products=[
                ProductRecommentationResource(upc="recommended_product1"),
            ],
            categories=[CategoryResource(code="1"), CategoryResource(code="2")],
            attributes={"henk": "Klaas", "harrie": 1},
        )

        _, errors = products_to_db(product_resource)
        self.assertEqual(len(errors), 0)
        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.images.count(), 2)
        self.assertEqual(prd.stockrecords.count(), 1)
        self.assertEqual(prd.categories.count(), 2)
        self.assertEqual(prd.attribute_values.count(), 2)
        self.assertEqual(prd.recommended_products.count(), 1)

        product_resource = ProductResource(
            upc="1234323-2",
            title="asdf2",
            slug="asdf-asdfasdf2",
            structure=Product.STANDALONE,
            product_class=ProductClassResource(slug="klaas"),
            categories=[],
            attributes={"henk": None, "harrie": None},
        )
        _, errors = products_to_db(product_resource, delete_related=True)
        self.assertEqual(len(errors), 0)

        self.assertEqual(prd.images.count(), 0)
        self.assertEqual(prd.stockrecords.count(), 0)
        self.assertEqual(prd.categories.count(), 0)
        self.assertEqual(prd.attribute_values.count(), 0)
        self.assertEqual(prd.recommended_products.count(), 0)

    def test_partial_deletion_of_one_to_many_related_models(self):
        partner = Partner.objects.get(name="klaas")
        product_class = ProductClassResource(slug="klaas", name="Klaas")
        product_resources = [
            ProductResource(
                upc="harrie",
                title="harrie",
                slug="asdf-harrie",
                structure=Product.STANDALONE,
                product_class=product_class,
                price=D("20"),
                availability=2,
                currency="EUR",
                partner=partner,
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="harrie",
                        original=File(self.image, name="harrie.jpg"),
                    ),
                ],
            ),
            ProductResource(
                upc="bat",
                title="bat",
                slug="asdf-bat",
                structure=Product.STANDALONE,
                product_class=product_class,
                price=D("10"),
                availability=2,
                currency="EUR",
                partner=partner,
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="bat",
                        original=File(self.image, name="bat.jpg"),
                    ),
                ],
            ),
            ProductResource(
                upc="hat",
                title="hat",
                slug="asdf-hat",
                structure=Product.STANDALONE,
                product_class=product_class,
                price=D("30"),
                availability=1,
                currency="EUR",
                partner=partner,
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="hat",
                        original=File(self.image, name="hat.jpg"),
                    ),
                ],
            ),
        ]
        _, errors = products_to_db(product_resources)
        self.assertEqual(len(errors), 0)
        self.assertEqual(Product.objects.count(), 3)

        product_resource = ProductResource(
            upc="hat",
            title="hat",
            slug="asdf-hat",
            structure=Product.STANDALONE,
            product_class=product_class,
        )
        _, errors = products_to_db(product_resource, delete_related=True)
        self.assertEqual(len(errors), 0)

        self.assertEqual(Product.objects.count(), 3)
        prd = Product.objects.get(upc="hat")
        self.assertEqual(prd.stockrecords.count(), 0)
        self.assertEqual(prd.images.count(), 0)
        # Other products' related models of stay unaffected
        self.assertTrue(Stockrecord.objects.count(), 2)
        self.assertTrue(ProductImage.objects.count(), 2)
    
    def test_only_category_related(self):
        partner = Partner.objects.get(name="klaas")
        product_class = ProductClassResource(slug="klaas", name="Klaas")
        Category.add_root(code="3", name="3")
        
        product_resources = [
            ProductResource(
                upc="harrie",
                title="harrie",
                slug="asdf-harrie",
                structure=Product.STANDALONE,
                product_class=product_class,
                price=D("20"),
                availability=2,
                currency="EUR",
                partner=partner,
                categories=[
                   CategoryResource(code="1"),
                   CategoryResource(code="3"),
                ],
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="harrie",
                        original=File(self.image, name="harrie.jpg"),
                    ),
                ],
            ),
            ProductResource(
                upc="bat",
                title="bat",
                slug="asdf-bat",
                structure=Product.STANDALONE,
                product_class=product_class,
                price=D("10"),
                availability=2,
                currency="EUR",
                partner=partner,
                categories=[
                   CategoryResource(code="2"),
                   CategoryResource(code="1")
                ],
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="bat",
                        original=File(self.image, name="bat.jpg"),
                    ),
                ],
            ),
            ProductResource(
                upc="hat",
                title="hat",
                slug="asdf-hat",
                structure=Product.STANDALONE,
                product_class=product_class,
                price=D("30"),
                availability=1,
                currency="EUR",
                partner=partner,
                categories=[
                   CategoryResource(code="3") 
                ],
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        code="hat",
                        original=File(self.image, name="hat.jpg"),
                    ),
                ],
            ),
        ]
        _, errors = products_to_db(product_resources)
        self.assertEqual(len(errors), 0)
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(ProductCategory.objects.count(), 5)
        self.assertEqual(ProductImage.objects.count(), 3)
        
        product_resources = [
            ProductResource(
                upc="harrie",
                title="harrie",
                structure=Product.STANDALONE,
                categories=[
                   CategoryResource(code="1"),
                ],
            ),
            ProductResource(
                upc="bat",
                title="bat",
                structure=Product.STANDALONE,
                categories=[
                   CategoryResource(code="2"),
                ],
            ),
            ProductResource(
                upc="hat",
                title="hat",
                structure=Product.STANDALONE,
                categories=[
                   CategoryResource(code="3") 
                ],
            ),
        ]

        _, errors = products_to_db(product_resources, fields_to_update=["Category.code"], delete_related=True)
        self.assertEqual(len(errors), 0)
        
        self.assertEqual(ProductCategory.objects.count(), 3)
        self.assertEqual(ProductImage.objects.count(), 3)
        