# pylint: skip-file
import io
import PIL

from decimal import Decimal as D

from django.core.management.base import BaseCommand
from django.core.files import File
from oscar.core.loading import get_model

from oscar_odin.mappings.catalogue import products_to_db
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Image as ImageResource,
    ProductClass as ProductClassResource,
    Category as CategoryResource,
    ProductAttributeValue as ProductAttributeValueResource,
)

from oscar_odin.mappings.defaults import DEFAULT_UPDATE_FIELDS
from oscar_odin.mappings.constants import *

from oscar_odin.utils import querycounter

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductImage = get_model("catalogue", "ProductImage")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")
Category = get_model("catalogue", "Category")
Partner = get_model("partner", "Partner")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class Command(BaseCommand):
    def handle(self, *args, **options):
        img = PIL.Image.new(mode="RGB", size=(200, 200))
        output = io.BytesIO()
        img.save(output, "jpeg")

        product_class, _ = ProductClass.objects.get_or_create(
            slug="klaas",
            defaults={"requires_shipping": True, "track_stock": True, "name": "Klaas"},
        )
        text_codes = ["code%s" % i for i in range(0, 10)]
        int_codes = ["code%s" % i for i in range(11, 20)]
        option_codes = ["code%s" % i for i in range(21, 30)]

        group, _ = AttributeOptionGroup.objects.get_or_create(name="gekke options")
        option, _ = AttributeOption.objects.get_or_create(group=group, option="klaas")

        for code in text_codes:
            ProductAttribute.objects.get_or_create(
                name=code,
                code=code,
                type=ProductAttribute.TEXT,
                product_class=product_class,
            )
        for code in int_codes:
            ProductAttribute.objects.get_or_create(
                name=code,
                code=code,
                type=ProductAttribute.INTEGER,
                product_class=product_class,
            )
        for code in option_codes:
            ProductAttribute.objects.get_or_create(
                name=code,
                code=code,
                type=ProductAttribute.OPTION,
                product_class=product_class,
                option_group=group,
            )

        product_class = ProductClassResource(slug="klaas", name="Klaas")

        partner, _ = Partner.objects.get_or_create(name="klaas")

        batsie = Category.add_root(
            name="Hatsie", slug="batsie", is_public=True, code="batsie"
        )
        henk = batsie.add_child(name="henk", slug="klaas", is_public=True, code="henk")
        henk.add_child(name="Knaken", slug="knaken", is_public=True, code="knaken")

        products = []

        def create_product(i):
            attributes = dict()
            attributes.update({code: "%s-%s" % (code, i) for code in text_codes})
            attributes.update({code: i for code in int_codes})
            attributes.update({code: option for code in option_codes})

            return ProductResource(
                upc="1234323-%s" % i,
                title="asdf2 %s" % i,
                slug="asdf-asdfasdf-%s" % i,
                description="description",
                structure=Product.STANDALONE,
                is_discountable=True,
                price=D("20%s" % i),
                availability=2,
                currency="EUR",
                partner=partner,
                product_class=product_class,
                images=[
                    ImageResource(
                        caption="gekke caption",
                        display_order=0,
                        original=File(output, name="image%s.jpg"),
                    ),
                ],
                categories=[
                    CategoryResource(code="batsie"),
                    CategoryResource(code="henk"),
                    CategoryResource(code="knaken"),
                ],
                attributes=attributes,
            )

        products = list(map(create_product, range(0, 5000)))

        with querycounter("COMMANDO"):
            products_to_db(
                products,
                fields_to_update=ALL_PRODUCT_FIELDS
                + ALL_STOCKRECORD_FIELDS
                + ALL_PRODUCTIMAGE_FIELDS,
            )

        print("AANTAL PRODUCTEN AANGEMAAKT:", Product.objects.count())
