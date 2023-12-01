from collections import defaultdict
from oscar.core.loading import get_model
from oscar_odin.mappings.context import get_instances_to_create_or_update

Product = get_model("catalogue", "Product")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


def validate_instances(instances, errors={}, validate_unique=True):
    validated_instances = []

    for instance in instances:
        instance.full_clean(validate_unique=validate_unique)
        validated_instances.append(instance)

    return validated_instances, errors


def save_foreign_keys(context, errors):
    for field in context.foreign_key_items.keys():
        fk_instances = context.foreign_key_items[field]
        validated_fk_instances, errors = validate_instances(fk_instances, errors)
        field.related_model.objects.bulk_create(validated_fk_instances)


def save_products(instances, context, errors):
    instances_to_create, instances_to_update = get_instances_to_create_or_update(
        Product, instances
    )

    validated_create_instances, errors = validate_instances(instances_to_create, errors)

    Product.objects.bulk_create(validated_create_instances)
    Product.objects.bulk_update(
        instances_to_update, fields=context.get_source_fields(Product)
    )


def save_one_to_many(context, errors):
    validated_o2m_instances = defaultdict(list)
    for relation, product, instances in context.get_all_o2m_instances:
        for instance in instances:
            setattr(instance, relation.field.name, product)
            try:
                instance.full_clean()
                validated_o2m_instances[relation] += [instance]
            except Exception as e:
                errors[instance] = e

    for relation in validated_o2m_instances.keys():
        relation.related_model.objects.bulk_create(validated_o2m_instances[relation])


def save_many_to_many(context, errors):
    m2m_to_create, m2m_to_update = context.get_all_m2m_relations
    validated_m2m_instances = []

    for relation, instances in m2m_to_create.items():
        validated_m2m_instances, errors = validate_instances(instances)
        relation.related_model.objects.bulk_create(validated_m2m_instances)

    for relation, instances in m2m_to_update.items():
        relation.related_model.objects.bulk_update(
            instances, fields=context.get_source_fields(relation.related_model)
        )

    for field, product, instances in context.get_all_m2m_instances:
        getattr(product, field.name).set(instances)

    return validated_m2m_instances, errors


def save_attributes(context, errors):
    attributes_to_create = []
    attributes_to_delete = []
    attributes_to_update = []
    fields_to_be_updated = set()

    for product, attr in context.attribute_data:
        (
            to_be_deleted,
            update_fields,
            to_be_updated,
            to_be_created,
        ) = product.attr.prepare_save()

        if to_be_deleted:
            attributes_to_delete.extend(to_be_deleted)

        if update_fields:
            fields_to_be_updated.add(update_fields)

        if to_be_updated:
            attributes_to_update.extend(to_be_updated)

        if to_be_created:
            attributes_to_create.extend(to_be_created)

    # now save all the attributes in bulk
    if to_be_deleted:
        ProductAttributeValue.objects.filter(pk__in=attributes_to_delete).delete()
    if to_be_updated:
        ProductAttributeValue.objects.bulk_update(
            attributes_to_update, fields_to_be_updated, batch_size=500
        )
    if to_be_created:
        ProductAttributeValue.objects.bulk_create(
            attributes_to_create, batch_size=500, ignore_conflicts=False
        )
