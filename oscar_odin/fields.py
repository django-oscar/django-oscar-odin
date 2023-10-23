"""Custom fields for Django Oscar."""
from decimal import Decimal, InvalidOperation
from typing import Optional

from odin.exceptions import ValidationError
from odin.fields import ScalarField


class DecimalField(ScalarField):
    """A field for decimals."""

    default_error_messages = {
        "invalid": "'%s' value must be a decimal.",
    }
    scalar_type = Decimal

    def __init__(self, places: int = 2, **kwargs):
        """Initialise the field."""
        super().__init__(**kwargs)
        self.places = places

    def to_python(self, value) -> Optional[Decimal]:
        """Convert value to a Decimal."""
        if value in self.empty_values:
            return
        try:
            return self.scalar_type(
                value,
            )

        except (TypeError, ValueError, InvalidOperation):
            msg = self.error_messages["invalid"] % value
            raise ValidationError(msg) from None

    def prepare(self, value):
        """Prepare value for serialization."""
        if value in self.empty_values:
            return

        if isinstance(value, self.scalar_type):
            return str(round(value, self.places))
