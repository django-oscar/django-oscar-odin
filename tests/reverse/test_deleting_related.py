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
)
from oscar_odin.mappings.constants import (
    ALL_CATEGORY_FIELDS,
    ALL_PRODUCTIMAGE_FIELDS,
    ALL_STOCKRECORD_FIELDS,
)

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
Category = get_model("catalogue", "Category")
Partner = get_model("partner", "Partner")
Stockrecord = get_model("partner", "Stockrecord")


class DeleteRelatedModelReverseTest(TestCase):
    @property
    def image(self):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")
        return output

    def test_deleting_product_related_models(self):
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
        )

        products_to_db(product_resource)
        prd = Product.objects.get(upc="1234323-2")

        self.assertEqual(prd.images.count(), 2)
        self.assertTrue(prd.images.filter(code="harrie").exists())
        self.assertTrue(prd.images.filter(code="vats").exists())

        self.assertEqual(prd.stockrecords.count(), 1)
        self.assertTrue(prd.stockrecords.filter(partner=partner).exists())

        self.assertEqual(prd.categories.count(), 2)
        self.assertTrue(prd.categories.filter(code="1").exists())
        self.assertTrue(prd.categories.filter(code="2").exists())

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

        product_resource = ProductResource(
            upc="1234323-2",
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
        )

        fields_to_update = ALL_PRODUCTIMAGE_FIELDS + ALL_STOCKRECORD_FIELDS

        products_to_db(
            product_resource, delete_related=True, fields_to_update=fields_to_update
        )

        # Related models are successfully deleted
        self.assertEqual(prd.images.count(), 1)
        self.assertTrue(prd.images.filter(code="harrie").exists())

        self.assertEqual(prd.stockrecords.count(), 1)
        self.assertTrue(prd.stockrecords.filter(partner=partner).exists())

        self.assertEqual(prd.attribute_values.count(), 1)
        self.assertEqual(prd.attr.henk, "Klaas")

        # Since categories were not added in Product resource, they remain unaffected
        self.assertEqual(prd.categories.count(), 2)
        self.assertTrue(prd.categories.filter(code="1").exists())
        self.assertTrue(prd.categories.filter(code="2").exists())

        # Adding categories and deleting one
        product_resource = ProductResource(
            upc="1234323-2",
            product_class=product_class,
            categories=[CategoryResource(code="1")],
        )
        products_to_db(
            product_resource, delete_related=True, fields_to_update=ALL_CATEGORY_FIELDS
        )
        self.assertEqual(prd.categories.count(), 1)
        self.assertTrue(prd.categories.filter(code="1").exists())
        self.assertEqual(prd.images.count(), 1)
        self.assertEqual(prd.stockrecords.count(), 1)
        self.assertEqual(prd.attribute_values.count(), 1)
