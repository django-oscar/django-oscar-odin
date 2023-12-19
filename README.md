# Oscar Odin

Mapping of Oscar eCommerce models to Odin resources.

## Installation

To install add `oscar_odin` to your installed apps

## Usage

```python
from oscar.core.loading import get_model
from oscar_odin.mappings import catalogue

Product = get_model("catalogue", "Product")

# Map a product to a resource.
product = Product.objects.get(id=1)
product_resource = catalogue.product_to_resource(product)
```

# Developing odin

## Using pip:

make install
make test

## Using poetry:

poetry install --all-extras
poetry run ./manage.py test