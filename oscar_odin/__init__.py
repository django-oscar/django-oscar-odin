"""Oscar Odin.

Odin Resources and mappings to Oscar models.
"""

from django.db.models import Model

from odin import registration
from odin.resources import ResourceBase
from odin.mapping import ResourceFieldResolver

from .field_resolvers import ModelFieldResolver, OdinResourceNestedFieldResolver
from .inheritable import InheritableResourceBase


class AddableList(list):
    """
    The registration.cache.field_resolvers is a set within Odin. Sets are unordered and random,
    which means registering our OdinResourceNestedFieldResolver one time would work, and another time it
    would get the original ResourceBase resolver (because it matches that type). This class converts the set to a list,
    and adding a .add method since that's used within register_field_resolver.
    """

    def add(self, item):
        self.append(item)


registration.cache.field_resolvers = AddableList(
    [(InheritableResourceBase, OdinResourceNestedFieldResolver)]
    + list(registration.cache.field_resolvers)
)
registration.register_field_resolver(ModelFieldResolver, Model)
