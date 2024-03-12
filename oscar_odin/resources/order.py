"""Resources for Oscar categories."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import odin

from ..fields import DecimalField
from ._base import OscarResource
from .address import BillingAddress, ShippingAddress
from .auth import User


class OscarOrder(OscarResource, abstract=True):
    """Base resource for Oscar order application."""

    class Meta:
        allow_field_shadowing = True
        namespace = "oscar.order"


class LinePrice(OscarOrder):
    """For tracking the prices paid for each unit within a line.

    This is necessary as offers can lead to units within a line
    having different prices.  For example, one product may be sold at
    50% off as it's part of an offer while the remainder are full price."""

    quantity: int
    price_incl_tax: Decimal = DecimalField(
        verbose_name="Price (inc. tax)",
    )
    price_excl_tax: Decimal = DecimalField(
        verbose_name="Price (inc. tax)",
    )
    shipping_incl_tax: Decimal = DecimalField(
        verbose_name="Shipping (inc. tax)",
    )
    shipping_excl_tax: Decimal = DecimalField(
        verbose_name="Shipping (inc. tax)",
    )
    tax_code: Optional[str] = odin.Options(
        verbose_name="VAT rate code",
    )


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
    stock_record_id: int
    product_id: int  # (expand this to full product resource)
    title: str
    upc: Optional[str]
    quantity: int = 1
    attributes: Dict[str, Any]
    prices: List[LinePrice]

    # Price information before discounts are applied
    price_before_discounts_incl_tax: Decimal = DecimalField(
        verbose_name="Price before discounts (inc. tax)"
    )
    price_before_discounts_excl_tax: Decimal = DecimalField(
        verbose_name="Price before discounts (excl. tax)"
    )

    # Normal site price for item (without discounts)
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


class PaymentEvent(OscarOrder):
    """A payment event for an order.

    For example:

    * All lines have been paid for
    * 2 lines have been refunded
    """

    amount: Decimal = DecimalField()
    reference: str = odin.Options(empty=True)
    # lines: List[Line]  # How to do this to prevent circular references
    event_type: str
    # shipping_event


class ShippingEvent(OscarOrder):
    """An event is something which happens to a group of lines such as
    1 item being dispatched.
    """

    # lines: List[Line]
    event_type: str
    notes: str = odin.Options(empty=True)
    date_created: datetime


class DiscountCategory(str, Enum):
    """Category of discount."""

    BASKET = "Basket"
    SHIPPING = "Shipping"
    DEFERRED = "Deferred"


class DiscountLine(OscarOrder):
    """Line of a discount"""

    line: Line
    order_discount_id: int
    is_incl_tax: bool
    amount: Decimal = DecimalField()


class DiscountPerTaxCodeResource(OscarOrder):
    """Total discount for each tax code in a discount"""

    amount: Decimal = DecimalField()
    tax_code: str


class Discount(OscarOrder):
    """A discount against an order."""

    id: int
    category: DiscountCategory
    offer_id: Optional[int]
    offer_name: Optional[str]
    voucher_id: Optional[int]
    voucher_code: Optional[str]
    frequency: Optional[int]
    amount: Decimal = DecimalField()
    message: str = odin.Options(empty=True)
    discount_lines: List[DiscountLine]
    is_basket_discount: bool
    is_shipping_discount: bool
    is_post_order_action: bool
    description: str
    discount_lines_per_tax_code: DiscountPerTaxCodeResource


class Surcharge(OscarOrder):
    """A surcharge against an order."""

    name: str
    code: str
    incl_tax: Decimal = DecimalField(
        verbose_name="Surcharge (inc. tax)",
    )
    excl_tax: Decimal = DecimalField(
        verbose_name="Surcharge (inc. tax)",
    )
    tax_code: Optional[str] = odin.Options(
        verbose_name="VAT rate code",
    )


class NoteType(str, Enum):
    """Type of order note."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    SYSTEM = "System"


class Note(OscarOrder):
    """A note against an order."""

    # user_id: int
    note_type: Optional[NoteType]
    message: str
    date_created: datetime
    date_updated: datetime


class StatusChange(OscarOrder):
    """A status change for an order."""

    old_status: str = odin.Options(empty=True)
    new_status: str = odin.Options(empty=True)
    date_created: datetime


class Order(OscarOrder):
    """An order within Django Oscar."""

    class Meta:
        allow_field_shadowing = True
        verbose_name = "Order"

    number: str = odin.Options(
        key=True,
        verbose_name="Order number",
    )
    site_id: Optional[int] = odin.Options(
        verbose_name="Site ID",
        doc_text="Site that the order was made through.",
    )
    user: Optional[User]
    email: str = odin.Options(empty=True)  # Map off the order property on model
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
    date_placed: datetime

    notes: List[Note]
    status_changes: List[StatusChange]
    discounts: List[Discount]
    surcharges: List[Surcharge]
    payment_events: List[PaymentEvent]
    shipping_events: List[ShippingEvent]
