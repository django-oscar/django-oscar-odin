from django.db.models import Prefetch

from oscar.core.loading import get_model, get_class
from oscar.apps.catalogue.managers import ProductQuerySet

ProductModel = get_model("catalogue", "Product")
CategoryModel = get_model("catalogue", "Category")
ProductAttributeValueModel = get_model("catalogue", "ProductAttributeValue")

get_public_children_prefetch = get_class(
    "oscar.apps.catalogue.prefetches", "get_public_children_prefetch"
)
get_browsable_categories_prefetch = get_class(
    "oscar.apps.catalogue.prefetches", "get_browsable_categories_prefetch"
)


def prefetch_product_queryset(
    queryset: ProductQuerySet, include_children=False
) -> ProductQuerySet:
    """
    To improve performance, all related fields that are used in the ProductModel to ProductToResource
    mapping are prefetched in a single query. Whenever you add a new related field to the mapping,
    make sure to add it here as well, and document the origin of that query like the others (if possible).
    This will improve performance significantly as it won't do n+1 queries.

    This function is loaded with get_class, so it can be customized per project.
    """
    queryset = queryset.select_related(
        # ProductToResource.product_class -> get_product_class
        "product_class",
    ).prefetch_related(
        # ProductToResource.images -> get_all_images
        Prefetch("images"),
        # ProducToResource.map_stock_price -> fetch_for_product
        Prefetch("stockrecords"),
        # ProducToResource.attributes -> get_attribute_values
        Prefetch(
            "attribute_values",
            queryset=ProductAttributeValueModel.objects.select_related(
                "attribute", "value_option"
            ),
        ),
        # ProductToResource.categories -> get_categories
        Prefetch("categories"),
        get_browsable_categories_prefetch(),
        # ProductToResource.map_stock_price -> fetch_for_parent -> product.children.public() -> stockrecords
        get_public_children_prefetch(
            queryset=ProductModel.objects.public().prefetch_related("stockrecords")
        ),
        # The parent and it's related fields are prefetched in numerous places in the resource.
        # ProductToResource.product_class -> get_product_class (takes parent product_class if itself has no product_class)
        # ProductToResource.images -> get_all_images (takes parent images if itself has no images)
        # ProductToResource.categories -> get_categories (takes parent categories if itself has no categories)
        Prefetch(
            "parent",
            queryset=ProductModel.objects.select_related(
                "product_class"
            ).prefetch_related(
                # ProductToResource.images -> get_all_images (takes parent images if itself has no images)
                Prefetch("images"),
                # ProductToResource.categories -> get_categories (takes parent categories if itself has no categories)
                get_browsable_categories_prefetch(),
            ),
        ),
    )

    if include_children:
        queryset = queryset.prefetch_related("children")

    return queryset
