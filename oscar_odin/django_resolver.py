"""Resolver for resolving attributes on Django models."""
from typing import Dict, Optional

from django.db.models import ForeignKey

from odin import Field
from odin.mapping import FieldResolverBase
from odin.utils import getmeta


class ModelFieldResolver(FieldResolverBase):
    """Field resolver for Django models."""

    def get_field_dict(self) -> Dict[str, Optional[Field]]:
        """Get a dictionary of fields from the source object."""
        meta = getmeta(self.obj)

        if meta.object_name == "Product":
            fields = {f: meta._forward_fields_map[f] for f in meta._forward_fields_map}
        else:
            fields = {f.name: f for f in meta.fields}

        fields.update(
            (r.related_name, r.field)
            for r in meta.related_objects
            if r.related_name != "+"
        )
        
        print(fields)

        return fields
