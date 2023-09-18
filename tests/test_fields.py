from decimal import Decimal

from django.test import SimpleTestCase
from odin.exceptions import ValidationError

from oscar_odin.fields import DecimalField


class TestDecimalField(SimpleTestCase):
    def test_to_python__where_value_is_string(self):
        field = DecimalField()

        actual = field.to_python("1.23")

        self.assertEqual(Decimal("1.23"), actual)

    def test_to_python__where_value_is_none(self):
        field = DecimalField()

        actual = field.to_python(None)

        self.assertIsNone(actual)

    def test_to_python__where_value_is_int(self):
        field = DecimalField()

        actual = field.to_python(42)

        self.assertEqual(Decimal("42"), actual)

    def test_to_python__where_value_is_float(self):
        field = DecimalField()

        actual = field.to_python(1.0)

        self.assertEqual(Decimal("1.0"), actual)

    def test_to_python__where_string_value_is_nonsense(self):
        field = DecimalField()

        with self.assertRaises(ValidationError):
            field.to_python("nonsense")

    def test_prepare__where_within_rounding(self):
        field = DecimalField()

        actual = field.prepare(Decimal("1.2359"))

        self.assertEqual("1.2359", actual)

    def test_prepare__where_value_is_rounded_to_default(self):
        field = DecimalField()

        actual = field.prepare(Decimal("3.121597"))

        self.assertEqual("3.1216", actual)

    def test_prepare__where_value_is_rounded_to_specific_number_of_places(self):
        field = DecimalField(places=2)

        actual = field.prepare(Decimal("6.62607015"))

        self.assertEqual("6.63", actual)
