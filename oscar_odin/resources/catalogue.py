"""Resources for Oscar categories."""
import enum
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from oscar.core.loading import get_model

import odin

from ..fields import DecimalField
from ._base import OscarResource

PartnerModel = get_model("partner", "Partner")
ProductClassModel = get_model("catalogue", "ProductClass")


class OscarCatalogue(OscarResource, abstract=True):
    """Base resource for Oscar catalogue application."""

    class Meta:
        namespace = "oscar.catalogue"


class Image(OscarCatalogue):
    """An image for a product."""

    class Meta:
        verbose_name = "Product image"
        verbose_name_plural = "Product images"

    id: int
    code: str
    original: Any
    caption: str = odin.Options(empty=True)
    display_order: int = odin.Options(
        default=0,
        doc_text=(
            "An image with a display order of zero will be the primary"
            " image for a product"
        ),
    )
    date_created: datetime


class Category(OscarCatalogue):
    """A category within Django Oscar."""

    id: int
    code: str
    name: str
    slug: str
    description: str
    meta_title: Optional[str]
    meta_description: Optional[str]
    image: Optional[str]
    is_public: bool
    ancestors_are_public: bool
    depth: int
    path: str


class ProductClass(OscarCatalogue):
    """A product class within Django Oscar."""

    name: str
    slug: str
    requires_shipping: bool
    track_stock: bool


class Structure(str, enum.Enum):
    """Structure of product."""

    STANDALONE = "standalone"
    PARENT = "parent"
    CHILD = "child"


class StockRecord(OscarCatalogue):
    id: int
    partner_sku: str
    num_in_stock: int
    num_allocated: int
    price: Decimal = DecimalField()
    currency: str


class ProductAttributeValue(OscarCatalogue):
    code: str
    value: Any


class ParentProduct(OscarCatalogue):
    upc: str


class Product(OscarCatalogue):
    """A product within Django Oscar."""

    id: int
    upc: Optional[str]
    structure: Structure
    title: str
    slug: str
    description: str = ""
    meta_title: Optional[str]
    images: List[Image] = odin.Options(empty=True)
    rating: Optional[float]
    is_discountable: bool = True
    is_public: bool = True
    parent: Optional[ParentProduct]

    # Price information
    price: Decimal = DecimalField()
    currency: str
    availability: Optional[int]
    partner: Optional[Any]

    product_class: Optional[ProductClass] = None
    attributes: Dict[str, Any]
    categories: List[Category]

    date_created: datetime
    date_updated: datetime

    children: Optional[List["Product"]] = odin.ListOf.delayed(
        lambda: Product, null=True
    )
