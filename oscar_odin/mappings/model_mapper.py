"""Extended model mapper for Django models."""
from typing import Sequence, cast

from django.db.models.fields.related import ForeignKey
from django.db.models.fields.reverse_related import (
    ManyToOneRel,
    ManyToManyRel,
)
from django.db.models.options import Options

from odin.mapping import MappingBase, MappingMeta
from odin.utils import getmeta


class ModelMappingMeta(MappingMeta):
    """Extended type of mapping meta."""

    def __new__(cls, name, bases, attrs):
        mapping_type = super().__new__(cls, name, bases, attrs)

        if mapping_type.to_obj is None:
            return mapping_type

        meta = cast(Options, getmeta(mapping_type.to_obj))

        # Extract out foreign field types.
        mapping_type.many_to_one_fields = many_to_one_fields = []
        mapping_type.one_to_many_fields = one_to_many_fields = []

        mapping_type.many_to_many_fields = [field for field in meta.many_to_many]
        mapping_type.foreign_key_fields = [
            field for field in meta.fields if isinstance(field, ForeignKey)
        ]

        # Break out related objects by their type
        for relation in meta.related_objects:
            if relation.related_name:
                if relation.many_to_one:
                    many_to_one_fields.append(relation)
                elif relation.one_to_many:
                    one_to_many_fields.append(relation)

        return mapping_type


class ModelMapping(MappingBase, metaclass=ModelMappingMeta):
    """Definition of a mapping between two Objects."""

    exclude_fields = []
    mappings = []

    # Specific fields
    one_to_many_fields: Sequence[ManyToManyRel] = []
    many_to_one_fields: Sequence[ManyToOneRel] = []
    many_to_many_fields: Sequence[ManyToManyRel] = []
    foreign_key_fields: Sequence[ForeignKey] = []

    register_mapping = False

    def create_object(self, **field_values):
        """Create a new product model."""
        related_field_values = self.get_related_field_values(field_values)

        parent = super().create_object(**field_values)

        self.add_related_field_values_to_context(parent, related_field_values)

        return parent

    def get_related_field_values(self, field_values):
        m2m_related_values = {
            field: field_values.pop(field.name)
            for field in self.many_to_many_fields
            if field.name in field_values
        }

        m2o_related_values = {
            relation: field_values.pop(relation.related_name)
            for relation in self.many_to_one_fields
            if relation.related_name in field_values
        }

        o2m_related_values = {
            relation: field_values.pop(relation.related_name)
            for relation in self.one_to_many_fields
            if relation.related_name in field_values
        }

        foreign_key_related_values = {
            field: field_values.get(field.name)
            for field in self.foreign_key_fields
            if field.name in field_values
        }

        return {
            "m2m_related_values": m2m_related_values,
            "m2o_related_values": m2o_related_values,
            "o2m_related_values": o2m_related_values,
            "fk_related_values": foreign_key_related_values,
        }

    def add_related_field_values_to_context(self, parent, related_field_values):
        for relation, instances in related_field_values["m2o_related_values"].items():
            if instances:
                self.context.add_instances_to_m2o_relation(
                    relation, (parent, instances)
                )

        for relation, instances in related_field_values["m2m_related_values"].items():
            self.context.add_instances_to_m2m_relation(relation, (parent, instances))

        for relation, instances in related_field_values["o2m_related_values"].items():
            self.context.add_instances_to_o2m_relation(relation, (parent, instances))

        for field, instance in related_field_values["fk_related_values"].items():
            if instance:
                self.context.add_instance_to_fk_items(field, instance)
