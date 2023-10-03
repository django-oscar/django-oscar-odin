"""Mappings between odin and django-oscar models."""
from typing import Iterable, Optional, Union

import odin
from django.http import HttpRequest
from oscar.core.loading import get_model

from .. import resources
from ._common import map_queryset

__all__ = (
    "OrderToResource",
    "order_to_resource",
)


OrderModel = get_model("order", "Order")
LineModel = get_model("order", "Line")
BillingAddressModel = get_model("order", "BillingAddress")
ShippingAddressModel = get_model("order", "ShippingAddress")


class BillingAddressToResource(odin.Mapping):
    """Mapping from billing address model to resource."""

    from_obj = BillingAddressModel
    to_obj = resources.order.BillingAddress


class ShippingAddressToResource(odin.Mapping):
    """Mapping from shipping address model to resource."""

    from_obj = ShippingAddressModel
    to_obj = resources.order.ShippingAddress


class OrderLineToResource(odin.Mapping):
    """Mapping from order line model to resource."""

    from_obj = OrderModel
    to_obj = resources.order.Order


class OrderToResource(odin.Mapping):
    """Mapping from order model to resource."""

    from_obj = OrderModel
    to_obj = resources.order.Order

    @odin.assign_field(to_list=True)
    def lines(self):
        """Map order lines."""
        items = self.source.get()
        return map_queryset(OrderLineToResource, items, context=self.context)


def order_to_resource(
    order: Union[OrderModel, Iterable[OrderModel]],
    request: Optional[HttpRequest] = None,
) -> Union[resources.order.Product, Iterable[resources.order.Product]]:
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
