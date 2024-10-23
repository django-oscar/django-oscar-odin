"""Oscar Odin.

Odin Resources and mappings to Oscar models.
"""

from django.db.models import Model

from odin import registration

from .django_resolver import ModelFieldResolver

registration.register_field_resolver(ModelFieldResolver, Model)
