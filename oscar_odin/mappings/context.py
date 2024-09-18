from collections import defaultdict
from operator import attrgetter

from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError

from oscar.core.loading import get_model
from oscar.apps.catalogue.product_attributes import QuerysetCache

from ..utils import ErrorLog, in_bulk
from ..exceptions import OscarOdinException
from .constants import MODEL_IDENTIFIERS_MAPPING

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
ProductAttribute = get_model("catalogue", "ProductAttribute")


def separate_instances_to_create_and_update(Model, instances, identifier_mapping):
    instances_to_create = []
    instances_to_update = []
    identifiying_keys = []

    identifiers = identifier_mapping.get(Model, {})

    if identifiers and instances:
        # pylint: disable=protected-access
        id_mapping = in_bulk(Model._default_manager, instances, identifiers)

        get_key_values = attrgetter(*identifiers)
        for instance in instances:
            key = get_key_values(instance)
            identifiying_keys.append(key)

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

        return instances_to_create, instances_to_update, identifiying_keys
    else:
        return instances, [], []


class ModelMapperContext(dict):
    foreign_key_items = None
    many_to_many_items = None
    many_to_one_items = None
    one_to_many_items = None
    attribute_data = None
    identifier_mapping = None
    instance_keys = None
    Model = None
    errors = None
    delete_related = False
    clean_instances = True

    update_related_models_same_type = True

    def __init__(
        self, Model, *args, delete_related=False, error_identifiers=None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.foreign_key_items = defaultdict(list)
        self.many_to_many_items = defaultdict(list)
        self.many_to_one_items = defaultdict(list)
        self.one_to_many_items = defaultdict(list)
        self.fields_to_update = defaultdict(list)
        self.identifier_mapping = defaultdict(tuple)
        self.attribute_data = []
        self.errors = ErrorLog(identifiers=error_identifiers)
        self.delete_related = delete_related
        self.Model = Model

    def __bool__(self):
        return True

    def prepare_instance_for_validation(self, instance):
        return instance

    def get_identity(self, instance, identifiers):
        if not identifiers:
            return
        return attrgetter(*identifiers)(instance)

    def validate_instances(self, instances, validate_unique=True, fields=None):
        if not self.clean_instances or not instances:
            return instances
        validated_instances = []
        identities = []
        exclude = ()
        if fields:
            all_fields = instances[0]._meta.fields
            exclude = [f.name for f in all_fields if f.name not in fields]

        identifiers = self.identifier_mapping.get(instances[0].__class__)

        for instance in instances:
            identity = self.get_identity(instance, identifiers)
            if identifiers is None or identity not in identities:
                if identifiers is not None:
                    identities.append(identity)
                try:
                    instance = self.prepare_instance_for_validation(instance)
                    instance.full_clean(
                        validate_unique=validate_unique, exclude=exclude
                    )
                except ValidationError as e:
                    self.errors.add_error(e, instance)
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
        identities = defaultdict(list)

        for relation in related_instance_items.keys():
            all_instances = []
            for _, instances in related_instance_items[relation]:
                all_instances.extend(instances)

            (
                instances_to_create,
                instances_to_update,
                identifying_keys,
            ) = separate_instances_to_create_and_update(
                relation.related_model, all_instances, self.identifier_mapping
            )

            to_create[relation].extend(instances_to_create)
            to_update[relation].extend(instances_to_update)
            identities[relation].extend(identifying_keys)

        return (to_create, to_update, identities)

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
                _,
            ) = separate_instances_to_create_and_update(
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

    def assign_pk_to_duplicate_instances(self, instances, validated_instances):
        """
        Assign pk to instances if it is None, based on the identity.
        e.g, instances contain two product classes, one with pk=2 and one with pk=None,
        both have same slug. This method will assign both pk=2 to both instances.
        """
        if not instances:
            return
        identifiers = self.identifier_mapping.get(instances[0].__class__)
        pk_identity_map = {
            self.get_identity(instance, identifiers): instance.pk
            for instance in validated_instances
        }
        for instance in instances:
            identity = self.get_identity(instance, identifiers)
            if instance.pk is None and identity in pk_identity_map:
                instance.pk = pk_identity_map[identity]

    def bulk_update_or_create_foreign_keys(self):
        instances_to_create, instances_to_update = self.get_fk_relations

        for field, instances in instances_to_create.items():
            validated_fk_instances = self.validate_instances(instances)
            field.related_model.objects.bulk_create(validated_fk_instances)
            if len(instances) != len(validated_fk_instances):
                self.assign_pk_to_duplicate_instances(instances, validated_fk_instances)

        for field, instances in instances_to_update.items():
            Model = field.related_model
            if self.update_related_models_same_type or Model != self.Model:
                fields = self.get_fields_to_update(Model)
                if fields is not None:
                    instances_to_update = self.validate_instances(
                        instances, fields=fields
                    )
                    Model.objects.bulk_update(instances_to_update, fields=fields)

    def bulk_update_or_create_instances(self, instances):
        (
            instances_to_create,
            instances_to_update,
            self.instance_keys,
        ) = separate_instances_to_create_and_update(
            self.Model, instances, self.identifier_mapping
        )

        validated_create_instances = self.validate_instances(instances_to_create)
        self.Model.objects.bulk_create(validated_create_instances)
        self.assign_pk_to_duplicate_instances(
            instances_to_create, validated_create_instances
        )
        for instance in validated_create_instances:
            if instance.pk is None:
                raise OscarOdinException(
                    """
                        oscar_odin.mappings.catalogue.products_to_db does not support sqlite3 with Django < 4.
                        Please use engines that have can_return_rows_from_bulk_insert set to True (like Postgres) or upgrade your Django version to 4 or higher.
                    """
                )

        fields = self.get_fields_to_update(self.Model)
        if fields is not None:
            validated_instances_to_update = self.validate_instances(
                instances_to_update, fields=fields
            )
            for instance in validated_instances_to_update:
                # This should be removed once support for django 3.2 is dropped
                # pylint: disable=protected-access
                instance._prepare_related_fields_for_save("bulk_update")
            self.Model.objects.bulk_update(validated_instances_to_update, fields=fields)

    def bulk_update_or_create_one_to_many(self):
        for relation, product, instances in self.get_all_o2m_instances:
            for instance in instances:
                setattr(instance, relation.field.name, product)

        instances_to_create, instances_to_update, identities = self.get_o2m_relations

        for relation, instances_to_create in instances_to_create.items():
            if (
                self.update_related_models_same_type
                or relation.related_model != self.Model
            ):
                fields = self.get_fields_to_update(relation.related_model)
                if fields is not None:
                    instances_to_create = self.validate_instances(instances_to_create)
                    relation.related_model.objects.bulk_create(instances_to_create)

        for relation, instances_to_update in instances_to_update.items():
            if (
                self.update_related_models_same_type
                or relation.related_model != self.Model
            ):
                fields = self.get_fields_to_update(relation.related_model)
                if fields is not None:
                    instances_to_update = self.validate_instances(
                        instances_to_update, fields=fields
                    )
                    relation.related_model.objects.bulk_update(
                        instances_to_update, fields=fields
                    )

        if self.delete_related:
            for relation, keys in identities.items():
                # instance_identifier here is product upc, if multiple identifiers for
                # a product are used, then the following code must be updated.
                instance_identifier = self.identifier_mapping.get(
                    relation.remote_field.related_model
                )[0]
                fields = self.get_fields_to_update(relation.related_model)
                if fields is not None:
                    conditions = Q()
                    identifiers = self.identifier_mapping[relation.related_model]
                    for key in keys:
                        if isinstance(key, (list, tuple)):
                            conditions |= Q(**dict(list(zip(identifiers, key))))
                        else:
                            conditions |= Q(**{f"{identifiers[0]}": key})
                    field_name = relation.remote_field.attname.replace(
                        "_", "__"
                    ).replace("id", instance_identifier)
                    # Delete all related one_to_many instances where product is in the
                    # given list of resources and excluding any instances present in
                    # those resources
                    relation.related_model.objects.filter(
                        **{f"{field_name}__in": self.instance_keys}
                    ).exclude(conditions).delete()

    def bulk_update_or_create_many_to_many(self):
        m2m_to_create, m2m_to_update, _ = self.get_all_m2m_relations

        # Create many to many's
        for relation, instances_to_create in m2m_to_create.items():
            if (
                self.update_related_models_same_type
                or relation.related_model != self.Model
            ):
                fields = self.get_fields_to_update(relation.related_model)
                if fields is not None:
                    instances_to_create = self.validate_instances(instances_to_create)
                    relation.related_model.objects.bulk_create(instances_to_create)

        # Update many to many's
        for relation, instances_to_update in m2m_to_update.items():
            if (
                self.update_related_models_same_type
                or relation.related_model != self.Model
            ):
                fields = self.get_fields_to_update(relation.related_model)
                if fields is not None:
                    instances_to_update = self.validate_instances(
                        instances_to_update, fields=fields
                    )
                    relation.related_model.objects.bulk_update(
                        instances_to_update, fields=fields
                    )

        for relation, values in self.many_to_many_items.items():
            fields = self.get_fields_to_update(relation.related_model)
            if fields is not None:
                Through = getattr(self.Model, relation.name).through

                # Create all through models that are needed for the products and
                # many to many
                throughs = defaultdict(Through)
                to_delete_throughs_product_ids = []
                for product, instances in values:
                    if not instances:
                        # Delete throughs if no instances are passed for the field
                        to_delete_throughs_product_ids.append(product.id)
                    for instance in instances:
                        throughs[(product.pk, instance.pk)] = Through(
                            **{
                                relation.m2m_field_name(): product,
                                relation.m2m_reverse_field_name(): instance,
                            }
                        )

                # Delete throughs if no instances are passed for the field
                if self.delete_related:
                    Through.objects.filter(
                        **{
                            "%s_id__in"
                            % relation.m2m_field_name(): to_delete_throughs_product_ids
                        }
                    ).all().delete()

                if throughs:
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

                    # Delete remaining non-existing through models
                    if self.delete_related:
                        Through.objects.filter(
                            **{
                                "%s_id__in"
                                % relation.m2m_field_name(): [
                                    item[0] for item in bulk_troughs.keys()
                                ]
                            }
                        ).exclude(id__in=bulk_troughs.values()).delete()

                    try:
                        # Save only new through models
                        Through.objects.bulk_create(throughs.values())
                    except ValueError as e:
                        raise OscarOdinException(
                            "Failed creating Trough models for %s. Maybe the related model does NOT exist?"
                            % relation.name
                        ) from e

    def bulk_save(
        self, instances, fields_to_update, identifier_mapping, clean_instances
    ):
        self.fields_to_update = fields_to_update
        self.identifier_mapping = identifier_mapping
        self.clean_instances = clean_instances

        with transaction.atomic():
            self.bulk_update_or_create_foreign_keys()

            self.bulk_update_or_create_instances(instances)

            self.bulk_update_or_create_one_to_many()

            self.bulk_update_or_create_many_to_many()

            return instances, self.errors


class ProductModelMapperContext(ModelMapperContext):
    update_related_models_same_type = False
    product_class_identifier = MODEL_IDENTIFIERS_MAPPING[ProductClass][0]
    product_class_keys = set()
    attributes = defaultdict(list)

    def prepare_instance_for_validation(self, instance):
        if hasattr(instance, "attr"):
            self.set_product_class_attributes(instance)
        return super().prepare_instance_for_validation(instance)

    def set_product_class_attributes(self, instance):
        if instance.product_class:
            key = getattr(instance.product_class, self.product_class_identifier)
            if key and key in self.attributes:
                instance.attr.cache.set_attributes(self.attributes[key])

    def add_instance_to_fk_items(self, field, instance):
        if instance is not None and not instance.pk:
            self.foreign_key_items[field] += [instance]
            if instance.__class__ == ProductClass:
                self.product_class_keys.add(
                    getattr(instance, self.product_class_identifier)
                )

    @property
    def get_fk_relations(self):
        to_create, to_update = super().get_fk_relations

        for relation, instances in to_create.items():
            if relation.related_model == self.Model and instances:
                raise OscarOdinException(
                    "Cannot create parents this way. Please create all parents first separately, then create the childs while linking the parents using the `oscar_odin.resources.catalogue.ParentProduct`"
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
            self.set_product_class_attributes(product)
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
        if attributes_to_delete and self.delete_related:
            ProductAttributeValue.objects.filter(pk__in=attributes_to_delete).delete()
        if attributes_to_update:
            validated_attributes_to_update = self.validate_instances(
                attributes_to_update
            )
            ProductAttributeValue.objects.bulk_update(
                validated_attributes_to_update, fields_to_be_updated, batch_size=500
            )
        if attributes_to_create:
            validated_attributes_to_create = self.validate_instances(
                attributes_to_create
            )
            ProductAttributeValue.objects.bulk_create(
                validated_attributes_to_create, batch_size=500, ignore_conflicts=False
            )

    def fetch_product_class_attributes(self):
        product_classes = ProductClass.objects.filter(
            **{f"{self.product_class_identifier}__in": self.product_class_keys}
        )

        for product_class in product_classes:
            self.attributes[
                getattr(product_class, self.product_class_identifier)
            ] = QuerysetCache(product_class.attributes.all())

    def bulk_update_or_create_instances(self, instances):
        self.fetch_product_class_attributes()
        super().bulk_update_or_create_instances(instances)

        self.bulk_update_or_create_product_attributes(instances)
