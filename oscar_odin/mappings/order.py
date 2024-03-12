"""Mappings between odin and django-oscar models."""
from typing import Any, Dict, Iterable, List, Optional, Union

import odin
from django.http import HttpRequest
from oscar.core.loading import get_model
from oscar_odin.resources.order import DiscountPerTaxCodeResource

from .. import resources
from ._common import map_queryset, OscarBaseMapping
from .address import BillingAddressToResource, ShippingAddressToResource
from .auth import UserToResource

from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce

__all__ = (
    "OrderToResource",
    "order_to_resource",
)

OrderModel = get_model("order", "Order")
OrderNoteModel = get_model("order", "OrderNote")
OrderStatusChangeModel = get_model("order", "OrderStatusChange")
LineModel = get_model("order", "Line")
LinePriceModel = get_model("order", "LinePrice")
PaymentEventModel = get_model("order", "PaymentEvent")
ShippingEventModel = get_model("order", "ShippingEvent")
OrderDiscountModel = get_model("order", "OrderDiscount")
OrderLineDiscountModel = get_model("order", "OrderLineDiscount")
SurchargeModel = get_model("order", "Surcharge")


class SurchargeToResource(OscarBaseMapping):
    """Mapping from a surcharge model to a resource."""

    from_obj = SurchargeModel
    to_obj = resources.order.Surcharge


class DiscountLineToResource(OscarBaseMapping):
    """Mapping from an order discount line model to a resource"""

    from_obj = OrderLineDiscountModel
    to_obj = resources.order.DiscountLine

    @odin.assign_field
    def line(self):
        """map line object as resource"""
        return LineToResource.apply(self.source.line)


class DiscountToResource(OscarBaseMapping):
    """Mapping from an order discount model to a resource."""

    from_obj = OrderDiscountModel
    to_obj = resources.order.Discount

    @odin.map_field
    def category(self, value: str):
        """Map category."""
        return resources.order.DiscountCategory(value)

    @odin.assign_field
    def is_basket_discount(self) -> bool:
        """map is basket discount function"""
        return self.source.is_basket_discount

    @odin.assign_field
    def is_shipping_discount(self) -> bool:
        """map is shipping discount function"""
        return self.source.is_shipping_discount

    @odin.assign_field
    def is_post_order_action(self) -> bool:
        """map is post order action function"""
        return self.source.is_post_order_action

    @odin.assign_field
    def description(self) -> str:
        """map description function"""
        return self.source.description()

    @odin.assign_field(to_list=True)
    def discount_lines(self):
        """map discount lines"""
        return map_queryset(
            DiscountLineToResource, self.source.discount_lines, context=self.context
        )

    @odin.assign_field(to_list=True)
    def discount_lines_per_tax_code(self):
        """get the total discount of all lines for each tax code"""
        discount_lines = []

        for tax_code in sorted(
            set(self.source.discount_lines.values_list("line__tax_code", flat=True))
        ):
            amount = self.source.discount_lines.filter(
                line__tax_code=tax_code
            ).aggregate(amount=Coalesce(Sum("amount"), Decimal(0)))["amount"]

            discount_lines.append(
                DiscountPerTaxCodeResource(amount=amount, tax_code=tax_code)
            )

        return discount_lines


class ShippingEventToResource(OscarBaseMapping):
    """Mapping from a shipping event model to a resource."""

    from_obj = ShippingEventModel
    to_obj = resources.order.ShippingEvent


class PaymentEventToResource(OscarBaseMapping):
    """Mapping from a payment event model to a resource."""

    from_obj = PaymentEventModel
    to_obj = resources.order.PaymentEvent


class LinePriceToResource(OscarBaseMapping):
    """Mapping from Line price to resource."""

    from_obj = LinePriceModel
    to_obj = resources.order.LinePrice


class LineToResource(OscarBaseMapping):
    """Mapping from Line model to resource."""

    from_obj = LineModel
    to_obj = resources.order.Line

    @odin.assign_field(to_list=True)
    def prices(self) -> List[resources.order.LinePrice]:
        """Map price resources."""
        items = self.source.prices.all()
        return map_queryset(LinePriceToResource, items, context=self.context)

    @odin.assign_field
    def attributes(self) -> Dict[str, Any]:
        """Map attributes."""


class StatusChangeToResource(OscarBaseMapping):
    """Mapping from order status change model to resource."""

    from_obj = OrderStatusChangeModel
    to_obj = resources.order.StatusChange


class NoteToResource(OscarBaseMapping):
    """Mapping from order note model to resource."""

    from_obj = OrderNoteModel
    to_obj = resources.order.Note


class OrderToResource(OscarBaseMapping):
    """Mapping from order model to resource."""

    from_obj = OrderModel
    to_obj = resources.order.Order

    @odin.assign_field
    def email(self) -> str:
        """Map order email."""
        return self.source.email

    @odin.assign_field
    def user(self) -> Optional[resources.auth.User]:
        """Map user."""
        if self.source.user:
            return UserToResource.apply(self.source.user)

    @odin.assign_field
    def billing_address(self) -> Optional[resources.address.BillingAddress]:
        """Map billing address."""
        if self.source.billing_address:
            return BillingAddressToResource.apply(self.source.billing_address)

    @odin.assign_field
    def shipping_address(self) -> Optional[resources.address.ShippingAddress]:
        """Map shipping address."""
        if self.source.shipping_address:
            return ShippingAddressToResource.apply(self.source.shipping_address)

    @odin.assign_field(to_list=True)
    def lines(self) -> List[resources.order.Line]:
        """Map order lines."""
        items = self.source.lines
        return map_queryset(LineToResource, items, context=self.context)

    @odin.assign_field(to_list=True)
    def notes(self) -> List[resources.order.Note]:
        """Map order notes."""
        items = self.source.notes
        return map_queryset(NoteToResource, items, context=self.context)

    @odin.assign_field(to_list=True)
    def status_changes(self) -> List[resources.order.StatusChange]:
        """Map order status changes."""
        items = self.source.status_changes
        return map_queryset(StatusChangeToResource, items, context=self.context)

    @odin.assign_field(to_list=True)
    def discounts(self) -> List[resources.order.Discount]:
        """Map order discounts."""
        items = self.source.discounts
        return map_queryset(DiscountToResource, items, context=self.context)

    @odin.assign_field(to_list=True)
    def surcharges(self) -> List[resources.order.Surcharge]:
        """Map order surcharges."""
        items = self.source.surcharges
        return map_queryset(SurchargeToResource, items, context=self.context)

    @odin.assign_field(to_list=True)
    def shipping_events(self) -> List[resources.order.ShippingEvent]:
        """Map order shipping events."""
        items = self.source.shipping_events
        return map_queryset(ShippingEventToResource, items, context=self.context)

    @odin.assign_field(to_list=True)
    def payment_events(self) -> List[resources.order.PaymentEvent]:
        """Map order payment events."""
        items = self.source.payment_events
        return map_queryset(PaymentEventToResource, items, context=self.context)


def order_to_resource(
    order: Union[OrderModel, Iterable[OrderModel]],
    request: Optional[HttpRequest] = None,
) -> Union[resources.order.Order, Iterable[resources.order.Order]]:
    """Map an order model to a resource.

    This method will except either a single order or an iterable of order
    models (eg a QuerySet), and will return the corresponding resource(s).

    :param order: A single product model or iterable of product models (eg a QuerySet).
    :param request: The current HTTP request
    """
    return OrderToResource.apply(
        order,
        context={},
    )
