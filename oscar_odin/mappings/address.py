"""Mappings between odin and django-oscar models."""
import odin
from oscar.core.loading import get_model, get_class, get_classes

__all__ = (
    "BillingAddressToResource",
    "ShippingAddressToResource",
)

BillingAddressModel = get_model("order", "BillingAddress")
ShippingAddressModel = get_model("order", "ShippingAddress")
CountryModel = get_model("address", "Country")

# mappings
OscarBaseMapping = get_class("oscar_odin.mappings._common", "OscarBaseMapping")

# resources
CountryResource, BillingAddressResource, ShippingAddressResource = get_classes(
    "oscar_odin.resources.address",
    ["CountryResource", "BillingAddressResource", "ShippingAddressResource"],
)


class CountryToResource(OscarBaseMapping):
    """Mapping from country model to resource."""

    from_obj = CountryModel
    to_obj = CountryResource


class BillingAddressToResource(OscarBaseMapping):
    """Mapping from billing address model to resource."""

    from_obj = BillingAddressModel
    to_obj = BillingAddressResource

    @odin.assign_field
    def country(self) -> CountryResource:
        """Map country."""
        return CountryToResource.apply(self.source.country)


class ShippingAddressToResource(OscarBaseMapping):
    """Mapping from shipping address model to resource."""

    from_obj = ShippingAddressModel
    to_obj = ShippingAddressResource

    @odin.assign_field
    def country(self) -> CountryResource:
        """Map country."""
        return CountryToResource.apply(self.source.country)
