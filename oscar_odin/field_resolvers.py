from copy import deepcopy
from typing import Dict, Optional

from odin import Field
from odin.fields.composite import ListOf, ArrayOf, DictAs, DictOf, ObjectAs
from odin.mapping import FieldResolverBase, ResourceFieldResolver
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


class OdinResourceNestedFieldResolver(ResourceFieldResolver):
    def get_field_dict(self):
        field_dict = super().get_field_dict()

        for field in getmeta(self.obj).composite_fields:
            if isinstance(field, (DictAs, ObjectAs, DictOf)):
                self._add_nested_fields(
                    field_dict=field_dict,
                    composite_field=field,
                    prefix=f"{field.name}.",
                )

        return field_dict

    def _add_nested_fields(self, field_dict, composite_field, prefix):
        fields = getmeta(composite_field.of).fields

        for field in fields:
            if isinstance(field, (ListOf, ArrayOf)):
                continue

            if isinstance(field, (DictAs, ObjectAs, DictOf)):
                self._add_nested_fields(
                    field_dict=field_dict,
                    composite_field=field,
                    prefix=f"{prefix}{field.name}.",
                )
            else:
                field_dict[f"{prefix}{field.name}"] = field
