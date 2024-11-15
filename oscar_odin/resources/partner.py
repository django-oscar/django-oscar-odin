from typing import Optional
from decimal import Decimal

from oscar.core.loading import get_model, get_class

from ..fields import DecimalField

OscarResource = get_class("oscar_odin.resources.base", "OscarResource")


class OscarPartnerResource(OscarResource, abstract=True):
    """Base resource for Oscar partner application."""

    class Meta:
        allow_field_shadowing = True
        namespace = "oscar.partner"


class PartnerResource(OscarPartnerResource):
    id: Optional[int]
    name: str
    code: str


class StockRecordResource(OscarPartnerResource):
    id: Optional[int]
    partner_sku: str
    num_in_stock: Optional[int]
    num_allocated: Optional[int]
    price: Decimal = DecimalField()
    currency: Optional[str]

    # It's optional because we allow easy price setting on the product resource by setting the partner model
    # on the product resource, which in turn is used to create a stockrecord with other price related fields.
    partner: Optional[PartnerResource]
