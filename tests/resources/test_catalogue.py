from django.test import TestCase

from oscar.core.loading import get_model

from odin.exceptions import ValidationError
from oscar_odin import resources

Product = get_model("catalogue", "Product")


class TestProduct(TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_init(self):
        target = resources.catalogue.ProductResource()

        self.assertIsNotNone(target)

    def test_resource_with_price_needs_other_fields_to_work(self):
        henk = resources.catalogue.ProductResource(
            upc="klaas", price=10, structure=Product.STANDALONE, title="BATSIE"
        )

        with self.assertRaises(ValidationError) as error:
            henk.full_clean()

        self.assertDictEqual(
            error.exception.error_messages,
            {
                "__all__": [
                    "upc, currency and partner are required when specifying price or availability"
                ],
                "partner": ["Partner can not be empty."],
            },
        )

        henk = resources.catalogue.ProductResource(
            upc="klaas",
            price=10,
            structure=Product.STANDALONE,
            currency="EUR",
            title="BATSIE",
        )

        with self.assertRaises(ValidationError) as error:
            henk.full_clean()

        self.assertDictEqual(
            error.exception.error_messages,
            {
                "__all__": [
                    "upc, currency and partner are required when specifying price or availability"
                ],
                "partner": ["Partner can not be empty."],
            },
        )

        henk = resources.catalogue.ProductResource(
            upc="klaas",
            price=10,
            structure=Product.STANDALONE,
            partner=1,
            title="BATSIE",
        )
        henk.full_clean()

    def test_resource_with_availability_needs_other_fields_to_work(self):
        henk = resources.catalogue.ProductResource(
            upc="klaas", availability=10, structure=Product.STANDALONE, title="BATSIE"
        )

        with self.assertRaises(ValidationError) as error:
            henk.full_clean()

        self.assertDictEqual(
            error.exception.error_messages,
            {
                "__all__": [
                    "upc, currency and partner are required when specifying price or availability"
                ],
                "partner": ["Partner can not be empty."],
            },
        )
