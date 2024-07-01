import unittest
from unittest.mock import MagicMock, patch, mock_open
from ecs.systems.generator_parsing_system import (
    compute_hash,
    construct_sections_map,
    parse_config_sections,
    process_sections,
    mark_remaining_sections_for_deletion,
    handle_config_entities,
    GeneratorParsingSystem
)
from ecs.components.raw_text_component import RawTextComponent
from ecs.components.index_component import IndexComponent
from ecs.components.section_type_component import SectionTypeComponent
from ecs.components.text_content_component import TextContentComponent
from ecs.components.command_component import CommandComponent
from ecs.components.instruction_component import InstructionComponent
from ecs.components.label_components import ClosingLabelComponent, OpeningLabelComponent
from ecs.components.mark_for_deletion_component import MarkedForDeletionComponent
from ecs.components.config_component import ConfigComponent
from ecs.event_bus import EventBus
from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager
from models.section import Section

class TestGeneratorParsingSystem(unittest.TestCase):

    @patch('ecs.systems.generator_parsing_system.hashlib.md5')
    def test_compute_hash(self, mock_md5):
        mock_md5.return_value.hexdigest.return_value = 'fakehash'
        with patch('builtins.open', mock_open(read_data='file content')):
            result = compute_hash('fake_path')
        self.assertEqual(result, 'fakehash')

    def test_construct_sections_map(self):
        component_manager = MagicMock()
        component_manager.get_component.side_effect = lambda entity, comp: RawTextComponent(entity, f"raw_text_{entity}", "hash")
        section_entities = [1, 2, 3]
        sections_map = construct_sections_map(section_entities, component_manager)
        self.assertEqual(len(sections_map), 3)

    def test_parse_config_sections(self):
        config_sections = [{'raw_text': '!key1=value1\n!key2=value2\n'}, {'raw_text': '!key3=value3\n'}]
        config_map = parse_config_sections(config_sections)
        self.assertEqual(config_map, {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'})

    def test_process_sections(self):
        entity_manager = MagicMock()
        component_manager = MagicMock()
        sections_data = [
            Section("raw_text_1", "type1", "content1", "command1", "instruction1", ["label1"], ["label2"]),
            Section("raw_text_2", "type2", "content2", "command2", "instruction2", ["label3"], ["label4"])
        ]
        known_sections_map = {}
        version_hash = "hash"
        process_sections(sections_data, known_sections_map, entity_manager, component_manager, version_hash)
        self.assertEqual(entity_manager.create_entity.call_count, 2)

    def test_mark_remaining_sections_for_deletion(self):
        component_manager = MagicMock(spec=ComponentManager)
        component_manager.has_component.return_value = False
        known_sections_map = {"raw_text_1": [(1, RawTextComponent(1, "raw_text_1", "hash"))]}
        mark_remaining_sections_for_deletion(known_sections_map, component_manager)
        self.assertTrue(component_manager.add_component.called)

    def test_handle_config_entities(self):
        entity_manager = MagicMock()
        component_manager = MagicMock()
        config_map = {'key1': 'value1'}
        component_manager.get_entities_with_component.return_value = []
        handle_config_entities(config_map, entity_manager, component_manager)
        self.assertTrue(component_manager.add_component.called)

    @patch('builtins.open', mock_open(read_data='file content'))
    @patch('ecs.systems.generator_parsing_system.compute_hash', return_value='hash')
    @patch('ecs.systems.generator_parsing_system.gen_split_into_sections', return_value=[{'raw_text': '!config\n'}, {'raw_text': 'section\n'}])
    @patch('ecs.systems.generator_parsing_system.parse_section', return_value=Section("raw_text", "type", "content", "command", "instruction", ["label1"], ["label2"]))
    def test_handle_file_modified_v2(self, mock_parse_section, mock_gen_split, mock_compute_hash):
        event_bus = MagicMock()
        entity_manager = MagicMock()
        component_manager = MagicMock()
        gps = GeneratorParsingSystem(event_bus)
        event_data = {'file_name': 'fake_file'}
        gps.handle_file_modified(event_data, entity_manager, component_manager)
        self.assertTrue(mock_compute_hash.called)
        self.assertTrue(mock_gen_split.called)
        self.assertTrue(mock_parse_section.called)

if __name__ == '__main__':
    unittest.main()
