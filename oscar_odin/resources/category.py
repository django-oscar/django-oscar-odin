"""Resources for Oscar categories."""
from datetime import datetime
from typing import List, Optional

import odin

from ._base import OscarResource


class OscarCategory(OscarResource, abstract=True):
    """Base resource for Oscar categories."""

    class Meta:
        namespace = "oscar.category"


class Image(OscarCategory):
    """An image for a product."""

    class Meta:
        verbose_name = "Product image"
        verbose_name_plural = "Product images"

    id: int
    original: str  # Image field (URL?)
    caption: str = odin.Options(empty=True)
    display_order: int = odin.Options(
        default=0,
        doc_text=(
            "An image with a display order of zero will be the primary"
            " image for a product"
        ),
    )
    date_created: datetime  # Optional in the case of creation?


class Product(OscarCategory):
    """A standalone product within Django Oscar."""

    id: int
    upc: Optional[str]
    title: str
    slug: str
    description: str = odin.Options(empty=True)
    meta_title: Optional[str]
    images: List[Image]
    rating: Optional[float]
    is_discountable: bool

    # product_class: ProductClass
    # attributes: List[ProductAttribute]
    # product_options: List[Option]
    # categories: List[Category]

    date_created: datetime
    date_updated: datetime
