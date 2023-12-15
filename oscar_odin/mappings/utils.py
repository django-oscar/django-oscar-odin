from collections import defaultdict

from django.db.models import prefetch_related_objects

from oscar.core.loading import get_model

from oscar_odin.mappings.context import get_instances_to_create_or_update
from oscar_odin.utils import querycounter, in_bulk

Product = get_model("catalogue", "Product")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


def validate_instances(instances, errors={}, validate_unique=True):
    validated_instances = []

    for instance in instances:
        instance.full_clean(validate_unique=validate_unique)
        validated_instances.append(instance)

    return validated_instances, errors


def save_foreign_keys(context, errors):
    instances_to_create, instances_to_update = context.get_fk_relations

    for field, instances in instances_to_create.items():
        validated_fk_instances, errors = validate_instances(instances, errors)
        field.related_model.objects.bulk_create(validated_fk_instances)

    for field, instances in instances_to_update.items():
        Model = field.related_model
        fields = context.get_fields_to_update(Model)
        if fields is not None:
            Model.objects.bulk_update(instances, fields=fields)


def save_products(instances, context, errors):
    instances_to_create, instances_to_update = get_instances_to_create_or_update(
        Product, instances, context.identifier_mapping
    )

    validated_create_instances, errors = validate_instances(instances_to_create, errors)

    Product.objects.bulk_create(validated_create_instances)

    fields = context.get_fields_to_update(Product)
    if fields is not None:
        Product.objects.bulk_update(instances_to_update, fields=fields)


def save_one_to_many(context, errors):
    for relation, product, instances in context.get_all_o2m_instances:
        for instance in instances:
            setattr(instance, relation.field.name, product)

    instances_to_create, instances_to_update = context.get_o2m_relations

    for relation, instances in instances_to_create.items():
        validated_instances_to_create, errors = validate_instances(instances, errors)
        relation.related_model.objects.bulk_create(instances)

    for relation, instances in instances_to_update.items():
        fields = context.get_fields_to_update(relation.related_model)
        if fields is not None:
            relation.related_model.objects.bulk_update(instances, fields=fields)


def save_many_to_many(context, errors):
    m2m_to_create, m2m_to_update = context.get_all_m2m_relations

    # Create many to many's
    for relation, instances in m2m_to_create.items():
        validated_m2m_instances, errors = validate_instances(instances)
        relation.related_model.objects.bulk_create(validated_m2m_instances)

    # Update many to many's
    for relation, instances in m2m_to_update.items():
        fields = context.get_fields_to_update(relation.related_model)
        if fields is not None:
            relation.related_model.objects.bulk_update(instances, fields=fields)

    for relation, values in context.many_to_many_items.items():
        Through = getattr(Product, relation.name).through

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
            field_names=(relation.m2m_field_name(), relation.m2m_reverse_field_name()),
        )

        # Remove existing through models
        for b in bulk_troughs.keys():
            if b in throughs:
                throughs.pop(b)

        # Save only new through models
        Through.objects.bulk_create(throughs.values())


def save_attributes(context, errors):
    attributes_to_create = []
    attributes_to_delete = []
    attributes_to_update = []
    fields_to_be_updated = set()

    for product, attr in context.attribute_data:
        product.attr.invalidate()
        (
            to_be_deleted,
            update_fields,
            to_be_updated,
            to_be_created,
        ) = product.attr.prepare_save()

        if to_be_deleted:
            attributes_to_delete.extend(to_be_deleted)

        if update_fields:
            fields_to_be_updated.update(update_fields)

        if to_be_updated:
            attributes_to_update.extend(to_be_updated)

        if to_be_created:
            attributes_to_create.extend(to_be_created)

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
