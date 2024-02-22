"""Mappings between odin and django-oscar models."""
import odin
from oscar.core.loading import get_model

from .. import resources
from ._common import OscarBaseMapping

__all__ = (
    "BillingAddressToResource",
    "ShippingAddressToResource",
)

BillingAddressModel = get_model("order", "BillingAddress")
ShippingAddressModel = get_model("order", "ShippingAddress")
CountryModel = get_model("address", "Country")


class CountryToResource(OscarBaseMapping):
    """Mapping from country model to resource."""

    from_obj = CountryModel
    to_obj = resources.address.Country


class BillingAddressToResource(OscarBaseMapping):
    """Mapping from billing address model to resource."""

    from_obj = BillingAddressModel
    to_obj = resources.address.BillingAddress

    @odin.assign_field
    def country(self) -> resources.address.Country:
        """Map country."""
        return CountryToResource.apply(self.source.country)


class ShippingAddressToResource(OscarBaseMapping):
    """Mapping from shipping address model to resource."""

    from_obj = ShippingAddressModel
    to_obj = resources.address.ShippingAddress

    @odin.assign_field
    def country(self) -> resources.address.Country:
        """Map country."""
        return CountryToResource.apply(self.source.country)
