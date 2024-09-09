from odin.codecs import dict_codec

from django.test import TestCase

from oscar.core.loading import get_model

from oscar_odin.mappings import catalogue

Product = get_model("catalogue", "Product")


class TestProduct(TestCase):
    fixtures = ["oscar_odin/catalogue"]

    def test_product_to_resource__basic_model_to_resource(self):
        product = Product.objects.first()

        actual = catalogue.product_to_resource(product)

        self.assertEqual(product.title, actual.title)

    def test_product_to_resource__basic_product_with_out_of_stock_children(self):
        product = Product.objects.get(id=1)

        actual = catalogue.product_to_resource(product)

        self.assertEqual(product.title, actual.title)

    def test_product_to_resource__where_is_a_parent_product_do_not_include_children(
        self,
    ):
        product = Product.objects.get(id=8)

        actual = catalogue.product_to_resource(product)

        self.assertEqual(product.title, actual.title)
        self.assertIsNone(actual.children)

    def test_mapping__where_is_a_parent_product_include_children(self):
        product = Product.objects.get(id=8)

        actual = catalogue.product_to_resource(product, include_children=True)

        self.assertEqual(product.title, actual.title)
        self.assertIsNotNone(actual.children)
        self.assertEqual(3, len(actual.children))

    def test_queryset_to_resources(self):
        queryset = Product.objects.all()
        product_resources = catalogue.product_queryset_to_resources(queryset)

        self.assertEqual(queryset.count(), len(product_resources))

    def test_queryset_to_resources_num_queries(self):
        queryset = Product.objects.all()
        self.assertEqual(queryset.count(), 210)

        # Without all the prefetching, the queries would be 1000+
        # For future reference; It's fine if this test fails after some changes.
        # However, the query shouldn't increase too much, if it does, it means you got a
        # n+1 query problem and that should be fixed instead by prefetching, annotating etc.
        with self.assertNumQueries(13):
            resources = catalogue.product_queryset_to_resources(
                queryset, include_children=False
            )
            dict_codec.dump(resources, include_type_field=False)

    def test_queryset_to_resources_include_children_num_queries(self):
        queryset = Product.objects.all()
        self.assertEqual(queryset.count(), 210)

        # It should only go up by a few queries.
        with self.assertNumQueries(19):
            resources = catalogue.product_queryset_to_resources(
                queryset, include_children=True
            )
            dict_codec.dump(resources, include_type_field=False)
