from django.db.models import Prefetch

from oscar.core.loading import get_model
from oscar.apps.catalogue.managers import ProductQuerySet

ProductModel = get_model("catalogue", "Product")
CategoryModel = get_model("catalogue", "Category")
ProductAttributeValueModel = get_model("catalogue", "ProductAttributeValue")


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
        "parent",
    ).prefetch_related(
        # ProductToResource.images -> get_all_images
        Prefetch("images"),
        # ProducToResource.map_stock_price -> fetch_for_product
        Prefetch("stockrecords"),
        # This gets prefetches somewhere (.categories.all()), it's not in get_categories as that does
        # .browsable() and that's where the prefetch_browsable_categories is for. But if we remove this,
        # the amount of queries will be more again. ToDo: Figure out where this is used and document it.
        Prefetch("categories"),
        # The parent and it's related fields are prefetched in numerous places in the resource.
        # ProductToResource.product_class -> get_product_class (takes parent product_class if itself has no product_class)
        # ProductToResource.images -> get_all_images (takes parent images if itself has no images)
        Prefetch("parent__product_class"),
        Prefetch("parent__images"),
    )

    # ProducToResource.attributes -> get_attribute_values
    queryset = queryset.prefetch_attribute_values(
        include_parent_children_attributes=include_children
    )

    # ProductToResource.categories -> get_categories
    # ProductToResource.categories -> get_categories -> looks up the parent categories if child
    queryset = queryset.prefetch_browsable_categories()
    # ProductToResource.map_stock_price -> fetch_for_parent -> product.children.public() -> stockrecords
    queryset = queryset.prefetch_public_children(
        queryset=ProductModel.objects.public().prefetch_related("stockrecords")
    )

    # When children are included, the same mapping that's applied for browsable products is applied on the children.
    # This means we'll have to prefetch (most) of the same fields for the children as well.
    if include_children:
        queryset = queryset.prefetch_related(
            "children__images",
            "children__stockrecords",
        )

    return queryset
