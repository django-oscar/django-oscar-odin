"""Resources for Oscar categories."""
from typing import Final, Sequence

import odin.validators
from odin.utils import iter_to_choices

from ._base import OscarResource


class OscarAddress(OscarResource, abstract=True):
    """Base resource for Oscar order application."""

    class Meta:
        allow_field_shadowing = True
        namespace = "oscar.address"


class Country(OscarAddress):
    """A country."""

    iso_3166_1_a2: str = odin.Options(
        key=True,
        validators=[odin.validators.MaxLengthValidator(2)],
        verbose_name="ISO 3166-1 alpha-2",
    )
    iso_3166_1_a3: str = odin.Options(
        validators=[odin.validators.MaxLengthValidator(3)],
        verbose_name="ISO 3166-1 alpha-3",
        empty=True,
    )
    iso_3166_1_numeric: str = odin.Options(
        validators=[odin.validators.MaxLengthValidator(3)],
        verbose_name="ISO 3166-1 numeric",
        empty=True,
    )
    printable_name: str = odin.Options(
        verbose_name="Country name",
        doc_text="Commonly used name e.g. United Kingdom",
    )
    name: str = odin.Options(
        verbose_name="Official name",
        doc_text=(
            "The full official name of a country e.g. "
            "United Kingdom of Great Britain and Northern Ireland"
        ),
    )
    is_shipping_country: bool = odin.Options(
        verbose_name="Is shipping country",
    )


TITLE_CHOICES: Final[Sequence[str]] = ("Mr", "Miss", "Mrs", "Ms", "Dr")


class Address(OscarAddress, abstract=True):
    """Base address resource."""

    title: str = odin.Options(empty=True, choices=iter_to_choices(TITLE_CHOICES))
    first_name: str = odin.Options(empty=True)
    last_name: str = odin.Options(empty=True)
    line1: str = odin.Options(verbose_name="First line of address")
    line2: str = odin.Options(empty=True, verbose_name="Second line of address")
    line3: str = odin.Options(empty=True, verbose_name="Third line of address")
    line4: str = odin.Options(empty=True, verbose_name="City")
    state: str = odin.Options(empty=True, verbose_name="State/Country")
    postcode: str = odin.Options(empty=True, verbose_name="Post/Zip-code")
    country: Country


class BillingAddress(Address):
    """Address for billing."""

    class Meta:
        allow_field_shadowing = True
        verbose_name = "Billing address"
        verbose_name_plural = "Billing addresses"


class ShippingAddress(Address):
    """Address for shipping."""

    class Meta:
        allow_field_shadowing = True
        verbose_name = "Shipping address"
        verbose_name_plural = "Shipping addresses"

    phone_number: str = odin.Options(
        empty=True,
        verbose_name="Phone number",
        doc_text="In case we need to call you about your order",
    )
    notes: str = odin.Options(
        empty=True,
        verbose_name="Instructions",
        doc_text="Tell us anything we should know when delivering your order.",
    )
