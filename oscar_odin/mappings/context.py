from collections import defaultdict
from operator import attrgetter

from odin.utils import getmeta

from oscar_odin.utils import in_bulk

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "StockRecord")
ProductClass = get_model("catalogue", "ProductClass")
ProductImage = get_model("catalogue", "ProductImage")


def get_instances_to_create_or_update(Model, instances, identifier_mapping):
    instances_to_create = []
    instances_to_update = []

    identifiers = identifier_mapping.get(Model, {})

    if identifiers:
        id_mapping = in_bulk(
            Model._default_manager, instances=instances, field_names=identifiers
        )

        get_key_values = attrgetter(*identifiers)
        for instance in instances:
            key = get_key_values(instance)

            if not isinstance(key, tuple):
                key = (key,)

            if key in id_mapping:
                instance.pk = id_mapping[key]
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.foreign_key_items = defaultdict(list)
        self.many_to_many_items = defaultdict(list)
        self.many_to_one_items = defaultdict(list)
        self.one_to_many_items = defaultdict(list)
        self.fields_to_update = defaultdict(list)
        self.identifier_mapping = defaultdict(tuple)
        self.attribute_data = []

    def __bool__(self):
        return True

    def add_attribute_data(self, attribute_data):
        self.attribute_data.append(attribute_data)

    def add_instances_to_m2m_relation(self, relation, instances):
        self.many_to_many_items[relation] += [instances]

    def add_instances_to_m2o_relation(self, relation, instances):
        self.many_to_one_items[relation] += [instances]

    def add_instances_to_o2m_relation(self, relation, instances):
        self.one_to_many_items[relation] += [instances]

    def add_instance_to_fk_items(self, field, instance):
        if not instance.pk:
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
        instance_update_pks = []

        for relation in related_instance_items.keys():
            all_instances = []
            for product, instances in related_instance_items[relation]:
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
        instance_update_pks = []

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
