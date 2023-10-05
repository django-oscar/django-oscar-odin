"""Resources for Oscar categories."""

from ._base import OscarResource


class OscarAddress(OscarResource, abstract=True):
    """Base resource for Oscar order application."""

    class Meta:
        namespace = "oscar.address"


class Country(OscarAddress):
    """A country."""

    iso_3166_1_a2: str
    iso_3166_1_a3: str
    iso_3166_1_numeric: str
    printable_name: str
    name: str
    is_shipping_country: str


class Address(OscarAddress, abstract=True):
    """Base address resource."""

    title: str
    first_name: str
    last_name: str
    line1: str
    line2: str
    line3: str
    line4: str
    state: str
    postcode: str
    country: Country


class BillingAddress(Address):
    """Address for billing."""


class ShippingAddress(Address):
    """Address for shipping."""

    phone_number: str
    notes: str
