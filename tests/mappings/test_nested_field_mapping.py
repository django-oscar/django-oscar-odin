import odin

from oscar_odin.inheritable import Resource
from oscar_odin.mappings.common import OscarBaseMapping

from django.test import TestCase


class ResourceA(Resource):
    title = odin.StringField()


class ResourceB(Resource):
    a = odin.DictOf(ResourceA)


class ResourceC(Resource):
    title = odin.StringField()


class BToCMapping(OscarBaseMapping):
    from_obj = ResourceB
    to_obj = ResourceC

    @odin.map_field(from_field="a.title", to_field="title")
    def title(self, title):
        return title


class NestedFieldMappingTestCase(TestCase):
    def test_valid_nested_field_mapping(self):
        a = ResourceA(title="I am a title")
        b = ResourceB(a=a)
        c = BToCMapping.apply(b)
        self.assertEqual(c.title, a.title)

    def test_nested_field_mapping_with_none_value(self):
        a = ResourceA(title="I am a title")
        b = ResourceB(a=None)
        with self.assertRaises(AttributeError):
            BToCMapping.apply(b)
