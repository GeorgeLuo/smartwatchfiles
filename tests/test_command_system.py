import unittest
from unittest.mock import MagicMock, patch
from ecs.systems.command_system import (
    get_model, handle_insert, handle_run, handle_gen, write_to_file, CommandSystem, LLMCacheValue
)
from ecs.components.command_component import CommandComponent
from ecs.components.instruction_component import InstructionComponent
from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager


class TestCommandSystem(unittest.TestCase):

    def setUp(self):
        self.component_manager = MagicMock(spec=ComponentManager)
        self.entity_manager = MagicMock(spec=EntityManager)
        self.entity = 'test_entity'
        self.cmd_comp = CommandComponent(
            command='insert', parameters=[('param1', ['value1'])])
        self.instruction_comp = InstructionComponent(
            instruction='echo Hello World')
        self.component_manager.get_component.side_effect = lambda entity, comp: self.instruction_comp if comp == InstructionComponent else self.cmd_comp

    def test_get_model_with_latest_parameter(self):
        parameters = [('llm', ['model1'])]
        model = get_model(self.component_manager, parameters, 'llm')
        self.assertEqual(model, 'model1')

    @patch('ecs.systems.command_system.get_config')
    def test_get_model_with_config(self, mock_get_config):
        mock_get_config.return_value = 'model2'
        parameters = []
        model = get_model(self.component_manager, parameters, 'llm')
        self.assertEqual(model, 'model2')

    @patch('ecs.systems.command_system.handle_insert_command')
    @patch('ecs.systems.command_system.set_rendered_text_component')
    def test_handle_insert(self, mock_set_rendered_text_component, mock_handle_insert_command):
        mock_handle_insert_command.return_value = 'Rendered Text'
        handle_insert(self.entity, self.component_manager, self.cmd_comp)
        mock_set_rendered_text_component.assert_called_with(
            self.component_manager, self.entity, 'Rendered Text')

    @patch('ecs.systems.command_system.subprocess.Popen')
    @patch('ecs.systems.command_system.set_rendered_text_component')
    def test_handle_run_success(self, mock_set_rendered_text_component, mock_popen):
        process_mock = MagicMock()
        attrs = {'communicate.return_value': ('output', ''), 'returncode': 0}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        handle_run(self.entity, self.component_manager, self.cmd_comp)
        mock_set_rendered_text_component.assert_called_with(
            self.component_manager, self.entity, 'Command executed successfully.\nOutput:\noutput')

    @patch('ecs.systems.command_system.subprocess.Popen')
    @patch('ecs.systems.command_system.set_rendered_text_component')
    def test_handle_run_failure(self, mock_set_rendered_text_component, mock_popen):
        process_mock = MagicMock()
        attrs = {'communicate.return_value': ('', 'error'), 'returncode': 1}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        handle_run(self.entity, self.component_manager, self.cmd_comp)
        mock_set_rendered_text_component.assert_called_with(
            self.component_manager, self.entity, 'Command failed with return code 1.\nError:\nerror')

    @patch('ecs.systems.command_system.call_llm')
    @patch('ecs.systems.command_system.build_query')
    @patch('ecs.systems.command_system.set_rendered_text_component')
    def test_handle_gen(self, mock_set_rendered_text_component, mock_build_query, mock_call_llm):
        mock_build_query.return_value = ('query', 'key')
        mock_call_llm.return_value = (False, 'Generated Text')
        llm_cache = {}

        handle_gen(self.entity, self.component_manager,
                   self.cmd_comp, llm_cache)
        mock_set_rendered_text_component.assert_called_with(
            self.component_manager, self.entity, 'Generated Text')

    @patch('ecs.systems.command_system.os.makedirs')
    @patch('ecs.systems.command_system.open', new_callable=unittest.mock.mock_open)
    def test_write_to_file(self, mock_open, mock_makedirs):
        write_to_file('test_dir/test_file.txt', 'content')
        mock_makedirs.assert_called_with('test_dir', exist_ok=True)
        mock_open.assert_called_with('test_dir/test_file.txt', 'w')
        mock_open().write.assert_called_with('content')

    def test_llm_cache_value(self):
        cache_value = LLMCacheValue('response', True)
        self.assertEqual(cache_value.response, 'response')
        self.assertTrue(cache_value.rate_limited)

    @patch('ecs.systems.command_system.set_rendered_text_component')
    def test_command_system_update(self, mock_set_rendered_text_component):
        command_system = CommandSystem()
        self.component_manager.get_entities_with_component.return_value = [
            self.entity]
        command_system.update(self.entity_manager, self.component_manager)
        mock_set_rendered_text_component.assert_called()


if __name__ == '__main__':
    unittest.main()
