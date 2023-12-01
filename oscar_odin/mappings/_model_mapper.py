"""Extended model mapper for Django models."""
from typing import Sequence, cast
from collections import defaultdict

from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import (
    OneToOneRel,
    ManyToOneRel,
    ManyToManyRel,
)
from django.db.models.options import Options

from oscar.core.loading import get_model

from odin.mapping import MappingBase, MappingMeta
from odin.utils import getmeta

Product = get_model("catalogue", "Product")


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
        mapping_type.many_to_many_fields = many_to_many_fields = [
            field for field in meta.many_to_many
        ]
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

    def create_object(self, **field_values):
        """Create a new product model."""
        attribute_values = field_values.pop("attributes", [])

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

        parent = super().create_object(**field_values)

        parent.attr.initialize()
        for key, value in attribute_values.items():
            parent.attr.set(key, value)

        self.context.add_attribute_data((parent, attribute_values))
        self.context.add_source_fields(Product, [self.source])

        for relation, instances in m2o_related_values.items():
            if instances:
                source_objects = getattr(self.source, relation.name)
                self.context.add_source_fields(relation.related_model, source_objects)
                self.context.add_instances_to_m2o_relation(
                    relation, (parent, instances)
                )

        for relation, instances in m2m_related_values.items():
            if instances:
                source_objects = getattr(self.source, relation.name)
                self.context.add_source_fields(relation.related_model, source_objects)
                self.context.add_instances_to_m2m_relation(
                    relation, (parent, instances)
                )

        for relation, instances in o2m_related_values.items():
            if instances:
                try:
                    source_objects = getattr(self.source, relation.name)
                    self.context.add_source_fields(
                        relation.related_model, source_objects
                    )
                except AttributeError:
                    pass

                self.context.add_instances_to_o2m_relation(
                    relation, (parent, instances)
                )

        for field in self.foreign_key_fields:
            if field.name in field_values:
                source_objects = getattr(self.source, field.name)
                self.context.add_source_fields(field.related_model, [source_objects])
                self.context.add_instance_to_fk_items(
                    field, field_values.get(field.name)
                )

        return parent
