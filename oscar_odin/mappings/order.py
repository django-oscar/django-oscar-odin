"""Mappings between odin and django-oscar models."""
from typing import Any, Dict, Iterable, List, Optional, Union

import odin
from django.http import HttpRequest
from oscar.core.loading import get_model

from .. import resources
from ._common import map_queryset
from .address import BillingAddressToResource, ShippingAddressToResource
from .auth import UserToResource

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
SurchargeModel = get_model("order", "Surcharge")


class SurchargeToResource(odin.Mapping):
    """Mapping from a surcharge model to a resource."""

    from_obj = SurchargeModel
    to_obj = resources.order.Surcharge


class DiscountToResource(odin.Mapping):
    """Mapping from an order discount model to a resource."""

    from_obj = OrderDiscountModel
    to_obj = resources.order.Discount

    @odin.map_field
    def category(self, value: str) -> resources.order.DiscountCategory:
        """Map category."""
        return resources.order.DiscountCategory(value)


class ShippingEventToResource(odin.Mapping):
    """Mapping from a shipping event model to a resource."""

    from_obj = ShippingEventModel
    to_obj = resources.order.ShippingEvent


class PaymentEventToResource(odin.Mapping):
    """Mapping from a payment event model to a resource."""

    from_obj = PaymentEventModel
    to_obj = resources.order.PaymentEvent


class LinePriceToResource(odin.Mapping):
    """Mapping from Line price to resource."""

    from_obj = LinePriceModel
    to_obj = resources.order.LinePrice


class LineToResource(odin.Mapping):
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


class StatusChangeToResource(odin.Mapping):
    """Mapping from order status change model to resource."""

    from_obj = OrderStatusChangeModel
    to_obj = resources.order.StatusChange


class NoteToResource(odin.Mapping):
    """Mapping from order note model to resource."""

    from_obj = OrderNoteModel
    to_obj = resources.order.Note


class OrderToResource(odin.Mapping):
    """Mapping from order model to resource."""

    from_obj = OrderModel
    to_obj = resources.order.Order

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
