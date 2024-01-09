from collections import defaultdict
from operator import attrgetter

from django.db import transaction
from django.core.exceptions import ValidationError

from oscar_odin.utils import in_bulk
from oscar_odin.exceptions import OscarOdinException

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


def get_instances_to_create_or_update(Model, instances, identifier_mapping):
    instances_to_create = []
    instances_to_update = []

    identifiers = identifier_mapping.get(Model, {})

    if identifiers:
        # pylint: disable=protected-access
        id_mapping = in_bulk(Model._default_manager, instances, identifiers)

        get_key_values = attrgetter(*identifiers)
        for instance in instances:
            key = get_key_values(instance)

            if not isinstance(key, tuple):
                key = (key,)

            if key in id_mapping:
                instance.pk = id_mapping[key]
                # pylint: disable=protected-access
                instance._state.db = "default"
                instance._state.adding = False
                instances_to_update.append(instance)
            else:
                instances_to_create.append(instance)

        return instances_to_create, instances_to_update
    else:
        return instances, []


class ModelMapperContext(dict):
    foreign_key_items = None
    many_to_many_items = None
    many_to_one_items = None
    one_to_many_items = None
    attribute_data = None
    identifier_mapping = None
    Model = None
    errors = None

    def __init__(self, Model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.foreign_key_items = defaultdict(list)
        self.many_to_many_items = defaultdict(list)
        self.many_to_one_items = defaultdict(list)
        self.one_to_many_items = defaultdict(list)
        self.fields_to_update = defaultdict(list)
        self.identifier_mapping = defaultdict(tuple)
        self.attribute_data = []
        self.errors = []
        self.Model = Model

    def __bool__(self):
        return True

    def validate_instances(self, instances, validate_unique=True):
        validated_instances = []

        for instance in instances:
            try:
                instance.full_clean(validate_unique=validate_unique)
            except ValidationError as e:
                self.errors.append(e)
            else:
                validated_instances.append(instance)

        return validated_instances

    def add_attribute_data(self, attribute_data):
        self.attribute_data.append(attribute_data)

    def add_instances_to_m2m_relation(self, relation, instances):
        self.many_to_many_items[relation] += [instances]

    def add_instances_to_m2o_relation(self, relation, instances):
        self.many_to_one_items[relation] += [instances]

    def add_instances_to_o2m_relation(self, relation, instances):
        self.one_to_many_items[relation] += [instances]

    def add_instance_to_fk_items(self, field, instance):
        if instance is not None and not instance.pk:
            self.foreign_key_items[field] += [instance]

    def get_fields_to_update(self, Model):
        modelname = "%s." % Model.__name__
        return [
            f.replace(modelname, "")
            for f in self.fields_to_update
            if f.startswith(modelname)
        ] or None

    def get_create_and_update_relations(self, related_instance_items):
        to_create = defaultdict(list)
        to_update = defaultdict(list)

        for relation in related_instance_items.keys():
            all_instances = []
            for _, instances in related_instance_items[relation]:
                all_instances.extend(instances)

            (
                instances_to_create,
                instances_to_update,
            ) = get_instances_to_create_or_update(
                relation.related_model, all_instances, self.identifier_mapping
            )

            to_create[relation].extend(instances_to_create)
            to_update[relation].extend(instances_to_update)

        return (to_create, to_update)

    @property
    def get_all_m2m_relations(self):
        return self.get_create_and_update_relations(self.many_to_many_items)

    @property
    def get_o2m_relations(self):
        return self.get_create_and_update_relations(self.one_to_many_items)

    @property
    def get_fk_relations(self):
        to_create = defaultdict(list)
        to_update = defaultdict(list)

        for relation, instances in self.foreign_key_items.items():
            (
                instances_to_create,
                instances_to_update,
            ) = get_instances_to_create_or_update(
                relation.related_model, instances, self.identifier_mapping
            )

            to_create[relation].extend(instances_to_create)
            to_update[relation].extend(instances_to_update)

        return (to_create, to_update)

    @property
    def get_all_o2m_instances(self):
        for relation in self.one_to_many_items:
            for product, instances in self.one_to_many_items[relation]:
                yield (relation, product, instances)

    def bulk_update_or_create_foreign_keys(self):
        instances_to_create, instances_to_update = self.get_fk_relations

        for field, instances in instances_to_create.items():
            validated_fk_instances = self.validate_instances(instances)
            field.related_model.objects.bulk_create(validated_fk_instances)

        for field, instances in instances_to_update.items():
            Model = field.related_model
            fields = self.get_fields_to_update(Model)
            if fields is not None:
                Model.objects.bulk_update(instances, fields=fields)

    def bulk_update_or_create_instances(self, instances):
        instances_to_create, instances_to_update = get_instances_to_create_or_update(
            self.Model, instances, self.identifier_mapping
        )

        validated_create_instances = self.validate_instances(instances_to_create)
        self.Model.objects.bulk_create(validated_create_instances)

        fields = self.get_fields_to_update(self.Model)
        if fields is not None:
            self.Model.objects.bulk_update(instances_to_update, fields=fields)

    def bulk_update_or_create_one_to_many(self):
        for relation, product, instances in self.get_all_o2m_instances:
            for instance in instances:
                setattr(instance, relation.field.name, product)

        instances_to_create, instances_to_update = self.get_o2m_relations

        for relation, instances in instances_to_create.items():
            validated_instances_to_create = self.validate_instances(instances)
            relation.related_model.objects.bulk_create(validated_instances_to_create)

        for relation, instances in instances_to_update.items():
            fields = self.get_fields_to_update(relation.related_model)
            if fields is not None:
                relation.related_model.objects.bulk_update(instances, fields=fields)

    def bulk_update_or_create_many_to_many(self):
        m2m_to_create, m2m_to_update = self.get_all_m2m_relations

        # Create many to many's
        for relation, instances in m2m_to_create.items():
            validated_m2m_instances = self.validate_instances(instances)
            relation.related_model.objects.bulk_create(validated_m2m_instances)

        # Update many to many's
        for relation, instances in m2m_to_update.items():
            fields = self.get_fields_to_update(relation.related_model)
            if fields is not None:
                relation.related_model.objects.bulk_update(instances, fields=fields)

        for relation, values in self.many_to_many_items.items():
            Through = getattr(self.Model, relation.name).through

            # Create all through models that are needed for the products and many to many
            throughs = defaultdict(Through)
            for product, instances in values:
                for instance in instances:
                    throughs[(product.pk, instance.pk)] = Through(
                        **{
                            relation.m2m_field_name(): product,
                            relation.m2m_reverse_field_name(): instance,
                        }
                    )

            # Bulk query the through models to see if some already exist
            bulk_troughs = in_bulk(
                Through.objects,
                instances=list(throughs.values()),
                field_names=(
                    relation.m2m_field_name(),
                    relation.m2m_reverse_field_name(),
                ),
            )

            # Remove existing through models
            for b in bulk_troughs.keys():
                if b in throughs:
                    throughs.pop(b)

            # Save only new through models
            Through.objects.bulk_create(throughs.values())

    def bulk_save(self, instances, fields_to_update, identifier_mapping):
        self.fields_to_update = fields_to_update
        self.identifier_mapping = identifier_mapping

        with transaction.atomic():
            self.bulk_update_or_create_foreign_keys()

            self.bulk_update_or_create_instances(instances)

            self.bulk_update_or_create_one_to_many()

            self.bulk_update_or_create_many_to_many()

            return instances, self.errors


class ProductModelMapperContext(ModelMapperContext):
    @property
    def get_fk_relations(self):
        to_create, to_update = super().get_fk_relations

        for relation, instances in to_create.items():
            if relation.related_model == self.Model and instances:
                raise OscarOdinException(
                    "Cannot create parents this way. Please create all parents first seperately, then create the childs while linking the parents using the `oscar_odin.resources.catalogue.ParentProduct`"
                )

        for relation, instances in to_update.items():
            if relation.related_model == self.Model:
                for instance in instances:
                    instance.refresh_from_db(fields=["product_class"])

        return to_create, to_update

    def bulk_update_or_create_product_attributes(self, instances):
        attributes_to_update = []
        attributes_to_create = []
        attributes_to_delete = []
        fields_to_be_updated = set()

        for product in instances:
            product.attr.invalidate()
            (
                to_be_updated,
                to_be_created,
                to_be_deleted,
                update_fields,
            ) = product.attr.prepare_save()

            if to_be_updated:
                attributes_to_update.extend(to_be_updated)

            if to_be_created:
                attributes_to_create.extend(to_be_created)

            if to_be_deleted:
                attributes_to_delete.extend(to_be_deleted)

            if update_fields:
                fields_to_be_updated.update(update_fields)

        # now save all the attributes in bulk
        if attributes_to_delete:
            ProductAttributeValue.objects.filter(pk__in=attributes_to_delete).delete()
        if attributes_to_update:
            ProductAttributeValue.objects.bulk_update(
                attributes_to_update, fields_to_be_updated, batch_size=500
            )
        if attributes_to_create:
            ProductAttributeValue.objects.bulk_create(
                attributes_to_create, batch_size=500, ignore_conflicts=False
            )

    def bulk_update_or_create_instances(self, instances):
        super().bulk_update_or_create_instances(instances)

        self.bulk_update_or_create_product_attributes(instances)
