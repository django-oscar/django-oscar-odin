"""Resources for Oscar categories."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

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

    partner_id: Optional[int]
    partner_name: str = odin.Options(empty=True)
    partner_sku: str
    partner_line_reference: str = odin.Options(
        empty=True,
        verbose_name="Partner reference",
    )
    partner_line_notes: str = odin.Options(
        empty=True,
        verbose_name="Partner notes",
    )
    # stockrecord_id: int
    # product_id: int
    title: str
    upc: Optional[str]
    quantity: int = 1
    line_price_incl_tax: Decimal = DecimalField(
        verbose_name="Price (inc. tax)",
    )
    line_price_excl_tax: Decimal = DecimalField(
        verbose_name="Price (excl. tax)",
    )
    line_price_before_discounts_incl_tax: Decimal = DecimalField(
        verbose_name="Price before discounts (inc. tax)"
    )
    line_price_before_discounts_excl_tax: Decimal = DecimalField(
        verbose_name="Price before discounts (excl. tax)"
    )
    unit_price_incl_tax: Decimal = DecimalField(
        verbose_name="Unit Price (inc. tax)",
    )
    unit_price_excl_tax: Decimal = DecimalField(
        verbose_name="Unit Price (excl. tax)",
    )
    tax_code: Optional[str] = odin.Options(
        verbose_name="VAT rate code",
    )
    status: str = odin.Options(empty=True)


class Order(OscarOrder):
    """An order within Django Oscar."""

    class Meta:
        verbose_name = "Order"

    number: str = odin.Options(
        key=True,
        verbose_name="Order number",
    )
    site_id: Optional[int] = odin.Options(
        verbose_name="Site ID",
        doc_text="Site that the order was made through.",
    )
    # basket:
    # user
    billing_address: Optional[BillingAddress]
    currency: str
    total_incl_tax: Decimal = DecimalField(
        verbose_name="Order total (inc. tax)",
    )
    total_excl_tax: Decimal = DecimalField(
        verbose_name="Order total (excl. tax)",
    )
    shipping_incl_tax: Decimal = DecimalField(
        verbose_name="Shipping charge (inc. tax)",
    )
    shipping_excl_tax: Decimal = DecimalField(
        verbose_name="hipping charge (excl. tax)",
    )
    shipping_tax_code: Optional[str] = odin.Options(
        verbose_name="Shipping VAT rate code"
    )
    shipping_address: Optional[ShippingAddress]
    shipping_method: str = odin.Options(empty=True)
    shipping_code: str = odin.Options(empty=True)
    lines: List[Line]
    status: str = odin.Options(empty=True)
    guest_email: str = odin.Options(empty=True)
    date_placed: datetime
