from collections import defaultdict
from operator import attrgetter

from odin.utils import getmeta

from oscar_odin.utils import in_bulk

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "StockRecord")

MODEL_IDENTIFIERS_MAPPING = {
    Category: ("slug",),
    Product: ("upc",),
    StockRecord: ("partner", "partner_sku"),
}


def get_unique_id_list(model, instances):
    identifiers = MODEL_IDENTIFIERS_MAPPING.get(model)
    unique_id_list = []
    for instance in instances:
        unique_id_list.append(
            [getattr(instance, identifier) for identifier in identifiers]
        )

    return unique_id_list, identifiers


def get_instances_to_create_or_update(Model, instances):
    instances_to_create = []
    instances_to_update = []

    unique_id_list, identifiers = get_unique_id_list(Model, instances)
    id_mapping = in_bulk(
        Model._default_manager, instances=instances, field_names=identifiers
    )

    get_key_values = attrgetter(*identifiers)
    for instance in instances:
        key = get_key_values(instance)
        if isinstance(key, str):
            key = (key,)

        if key in id_mapping:
            instance.pk = id_mapping[key]
            instance._state.db = "default"
            instance._state.adding = False
            instances_to_update.append(instance)
        else:
            instances_to_create.append(instance)

    return instances_to_create, instances_to_update


class ModelMapperContext(dict):
    foreign_key_items = None
    many_to_many_items = None
    many_to_one_items = None
    one_to_many_items = None
    source_fields = None
    attribute_data = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.foreign_key_items = defaultdict(list)
        self.many_to_many_items = defaultdict(list)
        self.many_to_one_items = defaultdict(list)
        self.one_to_many_items = defaultdict(list)
        self.source_fields = defaultdict(list)
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

    def get_filled_out_fields(self, source_objects):
        fields = set()
        for source in source_objects:
            meta = getmeta(source)
            fields.update([k for k, v in source.__dict__.items() if v is not None])

        return fields

    def add_source_fields(self, model, source_objects):
        self.source_fields[model] = self.get_filled_out_fields(source_objects)

    def get_source_fields(self, model):
        init_fields = self.source_fields[model]
        return [f.name for f in getmeta(model).concrete_fields if f.name in init_fields]

    @property
    def get_all_m2o_instances(self):
        for relation in self.many_to_one_items:
            for product, instances in self.many_to_one_items[relation]:
                yield (relation, product, instances)

    @property
    def get_all_m2m_instances(self):
        for relation in self.many_to_many_items:
            for product, instances in self.many_to_many_items[relation]:
                yield (relation, product, instances)

    @property
    def get_all_m2m_relations(self):
        m2m_to_create = defaultdict(list)
        m2m_to_update = defaultdict(list)

        for relation in self.many_to_many_items.keys():
            all_instances = []
            for product, instances in self.many_to_many_items[relation]:
                all_instances.extend(instances)

            (
                instances_to_create,
                instances_to_update,
            ) = get_instances_to_create_or_update(relation.related_model, all_instances)

            m2m_to_create[relation].extend(instances_to_create)
            m2m_to_update[relation].extend(instances_to_update)

        return (m2m_to_create, m2m_to_update)

    @property
    def get_all_o2m_instances(self):
        for relation in self.one_to_many_items:
            for product, instances in self.one_to_many_items[relation]:
                yield (relation, product, instances)
