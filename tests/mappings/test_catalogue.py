from odin.codecs import dict_codec

from django.test import TestCase

from oscar.core.loading import get_model

from oscar_odin.mappings import catalogue
from oscar_odin.mappings.helpers import (
    product_queryset_to_resources,
    product_to_resource,
)

from oscar_odin.utils import get_mapped_fields

Product = get_model("catalogue", "Product")


class TestProduct(TestCase):
    fixtures = ["oscar_odin/catalogue"]

    def test_product_to_resource__basic_model_to_resource(self):
        product = Product.objects.first()

        actual = product_to_resource(product)

        self.assertEqual(product.title, actual.title)

    def test_product_to_resource__basic_product_with_out_of_stock_children(self):
        product = Product.objects.get(id=1)

        actual = product_to_resource(product)

        self.assertEqual(product.title, actual.title)

    def test_product_to_resource__where_is_a_parent_product_do_not_include_children(
        self,
    ):
        product = Product.objects.get(id=8)

        actual = product_to_resource(product)

        self.assertEqual(product.title, actual.title)
        self.assertIsNone(actual.children)

    def test_mapping__where_is_a_parent_product_include_children(self):
        product = Product.objects.get(id=8)

        actual = product_to_resource(product, include_children=True)

        self.assertEqual(product.title, actual.title)
        self.assertIsNotNone(actual.children)
        self.assertEqual(3, len(actual.children))

    def test_queryset_to_resources(self):
        queryset = Product.objects.all()
        product_resources = product_queryset_to_resources(queryset)

        self.assertEqual(queryset.count(), len(product_resources))

    def test_queryset_to_resources_num_queries(self):
        queryset = Product.objects.all()
        self.assertEqual(queryset.count(), 210)

        # Without all the prefetching, the queries would be 1000+
        # For future reference; It's fine if this test fails after some changes.
        # However, the query shouldn't increase too much, if it does, it means you got a
        # n+1 query problem and that should be fixed instead by prefetching, annotating etc.
        with self.assertNumQueries(16):
            resources = product_queryset_to_resources(queryset, include_children=False)
            dict_codec.dump(resources, include_type_field=False)

    def test_queryset_to_resources_include_children_num_queries(self):
        queryset = Product.objects.all()
        self.assertEqual(queryset.count(), 210)

        # It should only go up by a few queries.
        with self.assertNumQueries(22):
            resources = product_queryset_to_resources(queryset, include_children=True)
            dict_codec.dump(resources, include_type_field=False)

    def test_get_mapped_fields(self):
        product_to_model_fields = get_mapped_fields(catalogue.ProductToModel)
        self.assertListEqual(
            sorted(product_to_model_fields),
            [
                "attributes",
                "categories",
                "children",
                "code",
                "date_created",
                "date_updated",
                "description",
                "id",
                "images",
                "is_discountable",
                "is_public",
                "meta_description",
                "meta_title",
                "parent",
                "priority",
                "product_class",
                "rating",
                "recommended_products",
                "slug",
                "stockrecords",
                "structure",
                "title",
                "upc",
            ],
        )

        model_to_product_fields = get_mapped_fields(catalogue.ProductToResource)
        self.assertListEqual(
            sorted(model_to_product_fields),
            [
                "attributes",
                "availability",
                "categories",
                "children",
                "code",
                "currency",
                "date_created",
                "date_updated",
                "description",
                "id",
                "images",
                "is_available_to_buy",
                "is_discountable",
                "is_public",
                "meta_description",
                "meta_title",
                "parent",
                "price",
                "priority",
                "product_class",
                "rating",
                "recommended_products",
                "slug",
                "stockrecords",
                "structure",
                "title",
                "upc",
            ],
        )

        fieldz = get_mapped_fields(catalogue.ProductToModel, *model_to_product_fields)
        self.assertListEqual(
            sorted(fieldz),
            [
                "attributes",
                "categories",
                "children",
                "code",
                "date_created",
                "date_updated",
                "description",
                "id",
                "images",
                "is_discountable",
                "is_public",
                "meta_description",
                "meta_title",
                "parent",
                "priority",
                "product_class",
                "rating",
                "recommended_products",
                "slug",
                "stockrecords",
                "structure",
                "title",
                "upc",
            ],
        )

        demfields = catalogue.ProductToModel.get_fields_impacted_by_mapping(
            *model_to_product_fields
        )
        self.assertListEqual(
            sorted(demfields),
            [
                "Category.code",
                "Product.code",
                "Product.description",
                "Product.is_discountable",
                "Product.is_public",
                "Product.meta_description",
                "Product.meta_title",
                "Product.parent",
                "Product.priority",
                "Product.slug",
                "Product.structure",
                "Product.title",
                "Product.upc",
                "ProductClass.slug",
                "ProductImage.caption",
                "ProductImage.code",
                "ProductImage.display_order",
                "ProductImage.original",
                "StockRecord.num_allocated",
                "StockRecord.num_in_stock",
                "StockRecord.partner",
                "StockRecord.partner_sku",
                "StockRecord.price",
                "StockRecord.price_currency",
            ],
        )
