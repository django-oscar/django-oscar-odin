"""Resolver for resolving attributes on Django models."""
from copy import deepcopy
from typing import Dict, Optional

from odin import Field
from odin.mapping import FieldResolverBase
from odin.utils import getmeta


class ModelFieldResolver(FieldResolverBase):
    """Field resolver for Django models."""

    # pylint: disable=protected-access
    def get_field_dict(self) -> Dict[str, Optional[Field]]:
        """Get a dictionary of fields from the source object."""
        meta = getmeta(self.obj)

        fields = deepcopy(meta._forward_fields_map)

        fields.update(
            (r.related_name, r.field)
            for r in meta.related_objects
            if r.related_name != "+"
        )

        return fields
