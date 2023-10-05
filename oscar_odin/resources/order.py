"""Resources for Oscar categories."""
from datetime import datetime
from decimal import Decimal
from typing import List

import odin

from ..fields import DecimalField
from ._base import OscarResource
from .address import BillingAddress, ShippingAddress


class OscarOrder(OscarResource, abstract=True):
    """Base resource for Oscar order application."""

    class Meta:
        namespace = "oscar.order"


class Line(OscarOrder):
    """A line within an order."""

    # partner_id: int
    partner_name: str
    partner_sku: str
    partner_line_reference: str
    partner_line_notes: str
    # stockrecord_id: int
    # product_id: int
    title: str
    upc: str
    quantity: int
    line_price_incl_tax: Decimal = DecimalField()
    line_price_excl_tax: Decimal = DecimalField()
    line_price_before_discounts_incl_tax: Decimal = DecimalField()
    line_price_before_discounts_excl_tax: Decimal = DecimalField()
    unit_price_incl_tax: Decimal = DecimalField()
    unit_price_excl_tax: Decimal = DecimalField()
    tax_code: str
    status: str


class Order(OscarOrder):
    """An order within Django Oscar."""

    class Meta:
        verbose_name = "Order"

    number: str = odin.Options(verbose_name="Order number")
    site_id: int = odin.Options(
        verbose_name="Site ID", doc_text="Site that the order was made through."
    )
    # basket:
    # user
    billing_address: BillingAddress
    currency: str
    total_incl_tax: Decimal = DecimalField()
    total_excl_tax: Decimal = DecimalField()
    shipping_incl_tax: Decimal = DecimalField()
    shipping_excl_tax: Decimal = DecimalField()
    shipping_tax_code: str
    shipping_address: ShippingAddress
    shipping_method: str
    shipping_code: str
    lines: List[Line]
    status: str
    guest_email: str
    date_placed: datetime
