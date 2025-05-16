"""Resources for Oscar categories."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import odin

from oscar.core.loading import get_class, get_classes

from ..fields import DecimalField

OscarResource = get_class("oscar_odin.resources.base", "OscarResource")
BillingAddressResource, ShippingAddressResource = get_classes(
    "oscar_odin.resources.address",
    ["BillingAddressResource", "ShippingAddressResource"],
)
UserResource = get_class("oscar_odin.resources.auth", "UserResource")
ProductResource = get_class("oscar_odin.resources.catalogue", "ProductResource")


class OscarOrderResource(OscarResource, abstract=True):
    """Base resource for Oscar order application."""

    class Meta:
        allow_field_shadowing = True
        namespace = "oscar.order"


class LinePriceResource(OscarOrderResource):
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


class LineResource(OscarOrderResource):
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
    product: ProductResource
    title: str
    upc: Optional[str]
    quantity: int = 1
    attributes: Dict[str, Any]
    prices: List[LinePriceResource]

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


class PaymentEventResource(OscarOrderResource):
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


class ShippingEventResource(OscarOrderResource):
    """An event is something which happens to a group of lines such as
    1 item being dispatched.
    """

    # lines: List[Line]
    event_type: str
    notes: str = odin.Options(empty=True)
    date_created: datetime


class DiscountCategoryResource(str, Enum):
    """Category of discount."""

    BASKET = "Basket"
    SHIPPING = "Shipping"
    DEFERRED = "Deferred"


class DiscountLineResource(OscarOrderResource):
    """Line of a discount"""

    line: LineResource
    order_discount_id: int
    is_incl_tax: bool
    amount: Decimal = DecimalField()


class DiscountPerTaxCodeResource(OscarOrderResource):
    """Total discount for each tax code in a discount"""

    amount: Decimal = DecimalField()
    tax_code: str


class DiscountResource(OscarOrderResource):
    """A discount against an order."""

    id: int
    category: DiscountCategoryResource
    offer_id: Optional[int]
    offer_name: Optional[str]
    voucher_id: Optional[int]
    voucher_code: Optional[str]
    frequency: Optional[int]
    amount: Decimal = DecimalField()
    message: str = odin.Options(empty=True)
    discount_lines: List[DiscountLineResource]
    is_basket_discount: bool
    is_shipping_discount: bool
    is_post_order_action: bool
    description: str
    discount_lines_per_tax_code: DiscountPerTaxCodeResource


class SurchargeResource(OscarOrderResource):
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


class NoteTypeResource(str, Enum):
    """Type of order note."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    SYSTEM = "System"


class NoteResource(OscarOrderResource):
    """A note against an order."""

    # user_id: int
    note_type: Optional[NoteTypeResource]
    message: str
    date_created: datetime
    date_updated: datetime


class StatusChangeResource(OscarOrderResource):
    """A status change for an order."""

    old_status: str = odin.Options(empty=True)
    new_status: str = odin.Options(empty=True)
    date_created: datetime


class OrderResource(OscarOrderResource):
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
    user: Optional[UserResource]
    email: str = odin.Options(empty=True)  # Map off the order property on model
    billing_address: Optional[BillingAddressResource]
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
    shipping_address: Optional[ShippingAddressResource]
    shipping_method: str = odin.Options(empty=True)
    shipping_code: str = odin.Options(empty=True)
    lines: List[LineResource]
    status: str = odin.Options(empty=True)
    date_placed: datetime

    notes: List[NoteResource]
    status_changes: List[StatusChangeResource]
    discounts: List[DiscountResource]
    surcharges: List[SurchargeResource]
    payment_events: List[PaymentEventResource]
    shipping_events: List[ShippingEventResource]
