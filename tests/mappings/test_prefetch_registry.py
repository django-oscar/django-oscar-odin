import unittest
from unittest.mock import Mock, patch, call
from django.db.models import Prefetch
from oscar.core.loading import get_class
from oscar_odin.mappings.prefetching.registry import PrefetchRegistry, prefetch_registry
from oscar_odin.mappings.prefetching.prefetch import prefetch_product_queryset

ProductQuerySet = get_class("catalogue.managers", "ProductQuerySet")


class TestPrefetchSystem(unittest.TestCase):
    def setUp(self):
        self.registry = PrefetchRegistry()
        self.mock_queryset = Mock(spec=ProductQuerySet)
        self.mock_queryset.select_related.return_value = self.mock_queryset
        self.mock_queryset.prefetch_related.return_value = self.mock_queryset

    def tearDown(self):
        # Clear the registry after each test
        prefetch_registry.prefetches.clear()
        prefetch_registry.children_prefetches.clear()
        prefetch_registry.select_related.clear()

    def test_register_string_prefetch(self):
        self.registry.register_prefetch("test_prefetch")
        self.assertIn("test_prefetch", self.registry.prefetches)
        self.assertEqual(self.registry.prefetches["test_prefetch"], "test_prefetch")

    def test_register_prefetch_object(self):
        prefetch = Prefetch("test_prefetch")
        self.registry.register_prefetch(prefetch)
        self.assertIn("test_prefetch", self.registry.prefetches)
        self.assertEqual(self.registry.prefetches["test_prefetch"], prefetch)

    def test_register_callable_prefetch(self):
        def test_prefetch(queryset, **kwargs):
            return queryset

        self.registry.register_prefetch(test_prefetch)
        self.assertIn("test_prefetch", self.registry.prefetches)
        self.assertEqual(self.registry.prefetches["test_prefetch"], test_prefetch)

    def test_register_children_prefetch(self):
        self.registry.register_children_prefetch("test_children_prefetch")
        self.assertIn("test_children_prefetch", self.registry.children_prefetches)

    def test_register_select_related_string(self):
        self.registry.register_select_related("test_select")
        self.assertIn("test_select", self.registry.select_related)

    def test_register_select_related_list(self):
        self.registry.register_select_related(["test_select1", "test_select2"])
        self.assertIn("test_select1", self.registry.select_related)
        self.assertIn("test_select2", self.registry.select_related)

    def test_unregister_prefetch(self):
        self.registry.register_prefetch("test_prefetch")
        self.registry.unregister_prefetch("test_prefetch")
        self.assertNotIn("test_prefetch", self.registry.prefetches)

    def test_unregister_children_prefetch(self):
        self.registry.register_children_prefetch("test_children_prefetch")
        self.registry.unregister_children_prefetch("test_children_prefetch")
        self.assertNotIn("test_children_prefetch", self.registry.children_prefetches)

    def test_unregister_select_related(self):
        self.registry.register_select_related("test_select")
        self.registry.unregister_select_related("test_select")
        self.assertNotIn("test_select", self.registry.select_related)

    def test_get_prefetches(self):
        self.registry.register_prefetch("test_prefetch")
        prefetches = self.registry.get_prefetches()
        self.assertIn("test_prefetch", prefetches)

    def test_get_children_prefetches(self):
        self.registry.register_children_prefetch("test_children_prefetch")
        children_prefetches = self.registry.get_children_prefetches()
        self.assertIn("test_children_prefetch", children_prefetches)

    def test_get_select_related(self):
        self.registry.register_select_related("test_select")
        select_related = self.registry.get_select_related()
        self.assertIn("test_select", select_related)

    def test_get_key_string(self):
        key = self.registry._get_key("test_key")
        self.assertEqual(key, "test_key")

    def test_get_key_prefetch_object(self):
        prefetch = Prefetch("test_prefetch")
        key = self.registry._get_key(prefetch)
        self.assertEqual(key, "test_prefetch")

    def test_get_key_callable(self):
        def test_callable():
            pass

        key = self.registry._get_key(test_callable)
        self.assertEqual(key, "test_callable")

    def test_get_key_unsupported_type(self):
        with self.assertRaises(ValueError):
            self.registry._get_key(123)

    @patch("oscar_odin.mappings.prefetching.prefetch.prefetch_registry")
    def test_prefetch_product_queryset_basic(self, mock_registry):
        mock_registry.get_select_related.return_value = ["product_class", "parent"]
        mock_registry.get_prefetches.return_value = {
            "images": "images",
            "stockrecords": "stockrecords",
        }
        mock_registry.get_children_prefetches.return_value = {}

        result = prefetch_product_queryset(self.mock_queryset)

        self.mock_queryset.select_related.assert_called_once_with(
            "product_class", "parent"
        )
        self.mock_queryset.prefetch_related.assert_has_calls(
            [call("images"), call("stockrecords")], any_order=True
        )

    @patch("oscar_odin.mappings.prefetching.prefetch.prefetch_registry")
    def test_prefetch_product_queryset_with_callable(self, mock_registry):
        def mock_callable(qs, **kwargs):
            return qs.prefetch_related("callable_prefetch")

        mock_registry.get_select_related.return_value = []
        mock_registry.get_prefetches.return_value = {"callable": mock_callable}
        mock_registry.get_children_prefetches.return_value = {}

        result = prefetch_product_queryset(self.mock_queryset)

        self.mock_queryset.prefetch_related.assert_called_once_with("callable_prefetch")

    @patch("oscar_odin.mappings.prefetching.prefetch.prefetch_registry")
    def test_prefetch_product_queryset_with_children(self, mock_registry):
        mock_registry.get_select_related.return_value = []
        mock_registry.get_prefetches.return_value = {}
        mock_registry.get_children_prefetches.return_value = {
            "children_images": "children__images",
            "children_stockrecords": "children__stockrecords",
        }

        result = prefetch_product_queryset(self.mock_queryset, include_children=True)

        self.mock_queryset.prefetch_related.assert_has_calls(
            [call("children__images"), call("children__stockrecords")], any_order=True
        )

    @patch("oscar_odin.mappings.prefetching.prefetch.prefetch_registry")
    def test_prefetch_product_queryset_with_prefetch_object(self, mock_registry):
        mock_queryset = Mock(spec=ProductQuerySet)
        prefetch_obj = Prefetch("custom_prefetch", queryset=mock_queryset)
        mock_registry.get_select_related.return_value = []
        mock_registry.get_prefetches.return_value = {"custom": prefetch_obj}
        mock_registry.get_children_prefetches.return_value = {}

        result = prefetch_product_queryset(self.mock_queryset)

        self.mock_queryset.prefetch_related.assert_called_once_with(prefetch_obj)

    @patch("oscar_odin.mappings.prefetching.prefetch.prefetch_registry")
    def test_prefetch_product_queryset_with_additional_kwargs(self, mock_registry):
        def mock_callable(qs, **kwargs):
            if kwargs.get("custom_arg"):
                return qs.prefetch_related("custom_prefetch")
            return qs

        mock_registry.get_select_related.return_value = []
        mock_registry.get_prefetches.return_value = {"callable": mock_callable}
        mock_registry.get_children_prefetches.return_value = {}

        result = prefetch_product_queryset(self.mock_queryset, custom_arg=True)

        self.mock_queryset.prefetch_related.assert_called_once_with("custom_prefetch")
