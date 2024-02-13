from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
ProductClass = get_model("catalogue", "ProductClass")
ProductImage = get_model("catalogue", "ProductImage")
StockRecord = get_model("partner", "StockRecord")
Partner = get_model("partner", "Partner")

PRODUCT_STRUCTURE = "Product.structure"
PRODUCT_IS_PUBLIC = "Product.is_public"
PRODUCT_UPC = "Product.upc"
PRODUCT_PARENT = "Product.parent"
PRODUCT_TITLE = "Product.title"
PRODUCT_SLUG = "Product.slug"
PRODUCT_DESCRIPTION = "Product.description"
PRODUCT_META_TITLE = "Product.meta_title"
PRODUCT_META_DESCRIPTION = "Product.meta_description"
PRODUCT_PARENT = "Product.parent"
PRODUCT_IS_DISCOUNTABLE = "Product.is_discountable"

PRODUCTCLASS_SLUG = "ProductClass.slug"
PRODUCTCLASS_REQUIRESSHIPPING = "ProductClass.requires_shipping"
PRODUCTCLASS_TRACKSTOCK = "ProductClass.track_stock"
PRODUCTCLASS_NAME = "ProductClass.name"

CATEGORY_NAME = "Category.name"
CATEGORY_CODE = "Category.code"
CATEGORY_DESCRIPTION = "Category.description"
CATEGORY_META_TITLE = "Category.meta_title"
CATEGORY_META_DESCRIPTION = "Category.meta_description"
CATEGORY_IMAGE = "Category.image"
CATEGORY_SLUG = "Category.slug"
CATEGORY_IS_PUBLIC = "Category.is_public"

PRODUCTIMAGE_CODE = "ProductImage.code"
PRODUCTIMAGE_ORIGINAL = "ProductImage.original"
PRODUCTIMAGE_CAPTION = "ProductImage.caption"
PRODUCTIMAGE_DISPLAY_ORDER = "ProductImage.display_order"

STOCKRECORD_PARTNER = "StockRecord.partner"
STOCKRECORD_PARTNER_SKU = "StockRecord.partner_sku"
STOCKRECORD_PRICE_CURRENCY = "StockRecord.price_currency"
STOCKRECORD_PRICE = "StockRecord.price"
STOCKRECORD_NUM_IN_STOCK = "StockRecord.num_in_stock"
STOCKRECORD_NUM_ALLOCATED = "StockRecord.num_allocated"

ALL_PRODUCT_FIELDS = [
    PRODUCT_STRUCTURE,
    PRODUCT_IS_PUBLIC,
    PRODUCT_UPC,
    PRODUCT_PARENT,
    PRODUCT_TITLE,
    PRODUCT_SLUG,
    PRODUCT_DESCRIPTION,
    PRODUCT_META_TITLE,
    PRODUCT_META_DESCRIPTION,
    PRODUCT_IS_DISCOUNTABLE,
    PRODUCT_PARENT,
]

ALL_PRODUCTCLASS_FIELDS = [
    PRODUCTCLASS_SLUG,
    PRODUCTCLASS_REQUIRESSHIPPING,
    PRODUCTCLASS_TRACKSTOCK,
    PRODUCTCLASS_NAME,
]

ALL_CATEGORY_FIELDS = [
    CATEGORY_NAME,
    CATEGORY_CODE,
    CATEGORY_DESCRIPTION,
    CATEGORY_META_TITLE,
    CATEGORY_META_DESCRIPTION,
    CATEGORY_IMAGE,
    CATEGORY_IS_PUBLIC,
    CATEGORY_SLUG,
]

ALL_PRODUCTIMAGE_FIELDS = [
    PRODUCTIMAGE_CODE,
    PRODUCTIMAGE_ORIGINAL,
    PRODUCTIMAGE_CAPTION,
    PRODUCTIMAGE_DISPLAY_ORDER,
]

ALL_STOCKRECORD_FIELDS = [
    STOCKRECORD_PARTNER,
    STOCKRECORD_PARTNER_SKU,
    STOCKRECORD_PRICE_CURRENCY,
    STOCKRECORD_PRICE,
    STOCKRECORD_NUM_IN_STOCK,
    STOCKRECORD_NUM_ALLOCATED,
]


ALL_CATALOGUE_FIELDS = (
    ALL_PRODUCT_FIELDS
    + ALL_PRODUCTIMAGE_FIELDS
    + ALL_STOCKRECORD_FIELDS
    + [PRODUCTCLASS_SLUG, CATEGORY_CODE]
)

MODEL_IDENTIFIERS_MAPPING = {
    Category: ("code",),
    Product: ("upc",),
    StockRecord: ("partner_id", "partner_sku"),
    ProductClass: ("slug",),
    ProductImage: ("code",),
    Partner: ("slug",),
}
