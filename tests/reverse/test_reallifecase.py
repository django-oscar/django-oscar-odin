import io
import odin
import requests
import responses

from urllib.parse import urlparse

from odin.codecs import csv_codec
from os import path
from decimal import Decimal as D

from django.core.files import File
from django.db import connection, reset_queries
from django.test import TestCase

from oscar.core.loading import get_model, get_class

from django.utils.text import slugify

from oscar_odin.fields import DecimalField
from oscar_odin.mappings.catalogue import products_to_db
from oscar_odin.resources.catalogue import (
    ProductResource,
    ProductImageResource,
    ProductClassResource,
    CategoryResource,
)

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
ProductImage = get_model("catalogue", "ProductImage")
Category = get_model("catalogue", "Category")
Partner = get_model("partner", "Partner")

create_from_breadcrumbs = get_class("catalogue.categories", "create_from_breadcrumbs")


class CSVProductResource(odin.Resource):
    id = odin.IntegerField()
    name = odin.StringField()
    category_id = odin.IntegerField()
    weight = odin.IntegerField()
    weight_type = odin.StringField()
    price = DecimalField()
    image = odin.StringField(null=True)
    app_image = odin.StringField(null=True)
    description = odin.StringField(null=True)
    ean = odin.StringField(null=True)
    number = odin.StringField(null=True)
    supplier_id = odin.IntegerField()
    active = odin.BooleanField()
    unit = odin.StringField()
    tags = odin.StringField(null=True)
    storage_type = odin.StringField()
    assortmentclass = odin.StringField()


class CSVProductMapping(odin.Mapping):
    from_obj = CSVProductResource
    to_obj = ProductResource

    mappings = (
        odin.define(from_field="number", to_field="upc"),
        odin.define(from_field="name", to_field="title"),
        odin.define(from_field="active", to_field="is_public"),
    )

    @odin.map_list_field(from_field="category_id")
    def categories(self, category_id):
        return [CategoryResource(code=category_id)]

    @odin.map_field(from_field="name")
    def slug(self, name):
        return slugify(name)

    @odin.map_field(
        from_field=["weight", "weight_type", "ean", "unit", "tags", "storage_type"]
    )
    def attributes(self, weight, weight_type, ean, unit, tags, storage_type):
        return {
            "weight": weight,
            "weight_type": weight_type,
            "ean": ean,
            "unit": unit,
            "tags": tags,
            "storage_type": storage_type,
        }

    @odin.map_list_field(from_field=["image", "app_image"])
    def images(self, image, app_image):
        images = []

        if image:
            response = requests.get(image)
            a = urlparse(image)
            img = File(io.BytesIO(response.content), name=path.basename(a.path))
            images.append(
                ProductImageResource(
                    display_order=0,
                    code="%s?upc=%s" % (self.source.number, image),
                    caption="",
                    original=img,
                )
            )

        if app_image and app_image != image:
            response = requests.get(app_image)
            a = urlparse(app_image)
            img = File(io.BytesIO(response.content), name=path.basename(a.path))
            images.append(
                ProductImageResource(
                    display_order=1,
                    caption="",
                    code="%s?upc=%s-2" % (self.source.number, image),
                    original=img,
                )
            )

        return images

    @odin.map_field(from_field="supplier_id")
    def partner(self, supplier_id):
        partner, _ = Partner.objects.get_or_create(name=supplier_id)
        return partner

    @odin.assign_field
    def product_class(self):
        return ProductClassResource(slug="standard")

    @odin.assign_field
    def structure(self):
        return Product.STANDALONE

    @odin.assign_field
    def is_discountable(self):
        return True


class RealLifeTest(TestCase):
    @responses.activate
    def test_mapping(self):
        responses.add(
            responses.GET,
            "https://picsum.photos/200/300",
            body="Dit is nep content van een image",
            status=200,
            content_type="image/jpeg",
        )

        for partner_id in ["1049", "1052", "1053", "1049"]:
            Partner.objects.get_or_create(
                code=partner_id, defaults={"name": partner_id}
            )

        # Create product class
        product_class, _ = ProductClass.objects.get_or_create(
            slug="standard",
            defaults={
                "name": "Standard product class",
                "requires_shipping": True,
                "track_stock": False,
            },
        )
        ProductAttribute.objects.get_or_create(
            code="weight",
            product_class=product_class,
            defaults={"name": "Weight", "type": ProductAttribute.INTEGER},
        )
        ProductAttribute.objects.get_or_create(
            code="weight_type",
            product_class=product_class,
            defaults={"name": "Weight type", "type": ProductAttribute.TEXT},
        )
        ProductAttribute.objects.get_or_create(
            code="ean",
            product_class=product_class,
            defaults={"name": "EAN", "type": ProductAttribute.TEXT},
        )
        ProductAttribute.objects.get_or_create(
            code="unit",
            product_class=product_class,
            defaults={"name": "Unit", "type": ProductAttribute.TEXT},
        )
        ProductAttribute.objects.get_or_create(
            code="tags",
            product_class=product_class,
            defaults={"name": "Tags", "type": ProductAttribute.TEXT},
        )
        ProductAttribute.objects.get_or_create(
            code="storage_type",
            product_class=product_class,
            defaults={"name": "Storage type", "type": ProductAttribute.TEXT},
        )

        # Create all the categories at first and assign a unique code
        for cat_id in ["101", "213", "264"]:
            cat = create_from_breadcrumbs(cat_id)
            cat.code = cat_id
            cat.save()

        # Get csv file and open it
        csv_file = self.get_csv_fixture("products.csv")
        with open(csv_file) as f:
            # Use odin codec to load in csv to our created resource
            products = csv_codec.reader(f, CSVProductResource, includes_header=True)

            # Map the csv resources to product resources
            product_resources = CSVProductMapping.apply(products)

            with self.assertNumQueries(59 * 20 + 12):
                # Map the product resources to products and save in DB
                _, errors = products_to_db(product_resources)
                self.assertEqual(len(errors), 0)

            self.assertEqual(Product.objects.all().count(), 59)
            self.assertEqual(ProductAttributeValue.objects.all().count(), 257)
            self.assertEqual(ProductImage.objects.all().count(), 52)


        with open(csv_file) as f:
            products_2 = csv_codec.reader(f, CSVProductResource, includes_header=True)
            
            # The seocnd time, the querycount should be lower
            product_resources_2 = CSVProductMapping.apply(products_2)

            with self.assertNumQueries(59 * 3 + 15):
                # Map the product resources to products and save in DB
                _, errors = products_to_db(product_resources_2, clean_instances=False)
                self.assertEqual(len(errors), 0)

            self.assertEqual(Product.objects.all().count(), 59)
            self.assertEqual(ProductAttributeValue.objects.all().count(), 257)
            self.assertEqual(ProductImage.objects.all().count(), 52)
    
    def get_csv_fixture(self, filename):
        return path.realpath(
            path.join(
                path.dirname(__file__),
                "../../",
                "oscar_odin/fixtures/oscar_odin/csv/",
                filename,
            )
        )
