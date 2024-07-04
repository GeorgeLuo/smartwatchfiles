import unittest
from unittest.mock import MagicMock
from ecs.utils.config_util import (
    get_config,
    _retrieve_config_entities,
    _no_entities_with_config,
    _get_first_entity,
    _retrieve_config_component,
    _get_config_value
)
from ecs.components.config_component import ConfigComponent
from ecs.managers.component_manager import ComponentManager


class TestConfigUtil(unittest.TestCase):

    def setUp(self):
        self.component_manager = MagicMock(spec=ComponentManager)
        self.config_component = MagicMock(spec=ConfigComponent)
        self.config_component.config_map = {'test_key': 'test_value'}
        self.entity = 'entity_1'

    def test_get_config_no_entities(self):
        self.component_manager.get_entities_with_component.return_value = []
        result = get_config(self.component_manager, 'test_key')
        self.assertIsNone(result)

    def test_get_config_with_entities(self):
        self.component_manager.get_entities_with_component.return_value = [
            self.entity]
        self.component_manager.get_component.return_value = self.config_component
        result = get_config(self.component_manager, 'test_key')
        self.assertEqual(result, 'test_value')

    def test_retrieve_config_entities(self):
        self.component_manager.get_entities_with_component.return_value = [
            self.entity]
        result = _retrieve_config_entities(self.component_manager)
        self.assertEqual(result, [self.entity])

    def test_no_entities_with_config_true(self):
        result = _no_entities_with_config([])
        self.assertTrue(result)

    def test_no_entities_with_config_false(self):
        result = _no_entities_with_config([self.entity])
        self.assertFalse(result)

    def test_get_first_entity(self):
        result = _get_first_entity([self.entity])
        self.assertEqual(result, self.entity)

    def test_retrieve_config_component(self):
        self.component_manager.get_component.return_value = self.config_component
        result = _retrieve_config_component(
            self.component_manager, self.entity)
        self.assertEqual(result, self.config_component)

    def test_get_config_value(self):
        result = _get_config_value(self.config_component, 'test_key')
        self.assertEqual(result, 'test_value')
