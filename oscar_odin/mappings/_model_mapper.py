"""Extended model mapper for Django models."""
from typing import Sequence

from django.db.models import ManyToManyRel, ManyToOneRel, OneToOneRel
from odin.mapping import MappingBase, MappingMeta
from odin.utils import getmeta


class ModelMappingMeta(MappingMeta):
    """Extended type of mapping meta."""

    def __new__(cls, name, bases, attrs):
        mapping_type = super().__new__(cls, name, bases, attrs)

        if mapping_type.to_obj is None:
            return mapping_type

        # Extract out foreign field types.
        mapping_type.one_to_one_fields = one_to_one_fields = []
        mapping_type.many_to_one_fields = many_to_one_fields = []
        mapping_type.many_to_many_fields = many_to_many_fields = []
        for relation in getmeta(mapping_type.to_obj).related_objects:
            if isinstance(relation, OneToOneRel):
                one_to_one_fields.append(relation.related_name)
            elif isinstance(relation, ManyToOneRel):
                many_to_one_fields.append(relation.related_name)
            elif isinstance(relation, ManyToManyRel):
                many_to_many_fields.append(relation.related_name)

        return mapping_type


class ModelMapping(MappingBase, metaclass=ModelMappingMeta):
    """Definition of a mapping between two Objects."""

    exclude_fields = []
    mappings = []
    one_to_one_fields: Sequence[str] = []
    many_to_one_fields: Sequence[str] = []
    many_to_many_fields: Sequence[str] = []

    def create_object(self, **field_values):
        """Create a new product model."""

        [
            (name, field_values.pop(name))
            for name in self.one_to_one_fields
            if name in field_values
        ]
        many_to_one_values = [
            (name, field_values.pop(name))
            for name in self.many_to_one_fields
            if name in field_values
        ]
        [
            (name, field_values.pop(name))
            for name in self.many_to_many_fields
            if name in field_values
        ]

        obj = super().create_object(**field_values)

        # TODO add one_to_one_values
        for name, value in many_to_one_values:
            if value:
                getattr(obj, name).set(value)
        # TODO add many_to_many_values

        return obj
