import unittest
from unittest.mock import MagicMock, patch
from ecs.systems.label_embedding_system import (
    reset_text_if_embeddings_changed,
    process_labels_in_text,
    process_labels_in_instruction,
    LabelEmbeddingSystem
)
from ecs.components.instruction_component import InstructionComponent
from ecs.components.text_content_component import TextContentComponent
from ecs.managers.component_manager import ComponentManager, Entity
from ecs.managers.entity_manager import EntityManager


class TestLabelEmbeddingSystem(unittest.TestCase):

    @patch('ecs.systems.label_embedding_system.embeddings_have_changed')
    def test_reset_text_if_embeddings_changed(self, mock_embeddings_have_changed):
        component_manager = MagicMock(spec=ComponentManager)
        entity = MagicMock(spec=Entity)
        component_type = TextContentComponent

        # Test case where embeddings have changed
        mock_embeddings_have_changed.return_value = True
        component_manager.get_component.return_value.text_content = "New Text Content"
        result = reset_text_if_embeddings_changed(
            component_manager, entity, component_type)
        self.assertEqual(result, "New Text Content")

        # Test case where embeddings have not changed but RenderedTextComponent exists
        mock_embeddings_have_changed.return_value = False
        component_manager.has_component.return_value = True
        component_manager.get_component.return_value.rendered_text = "Rendered Text"
        result = reset_text_if_embeddings_changed(
            component_manager, entity, component_type)
        self.assertEqual(result, "Rendered Text")

        # Test case where embeddings have not changed and RenderedTextComponent does not exist
        component_manager.has_component.return_value = False
        component_manager.get_component.return_value.text_content = "Original Text Content"
        result = reset_text_if_embeddings_changed(
            component_manager, entity, component_type)
        self.assertEqual(result, "Original Text Content")

    @patch('ecs.systems.label_embedding_system.get_replacement_text_by_label')
    @patch('ecs.systems.label_embedding_system.set_rendered_text_component')
    @patch('ecs.systems.label_embedding_system.add_linked_label')
    def test_process_labels_in_text(self, mock_add_linked_label, mock_set_rendered_text_component, mock_get_replacement_text_by_label):
        component_manager = MagicMock(spec=ComponentManager)
        entity = MagicMock(spec=Entity)
        base_text = "This is a :label: test."

        # Test case where replacement text is found
        mock_get_replacement_text_by_label.return_value = "replacement"
        process_labels_in_text(component_manager, entity, base_text)
        mock_set_rendered_text_component.assert_called_with(
            component_manager, entity, "This is a replacement test.")
        mock_add_linked_label.assert_called_with(
            component_manager, entity, "label", "replacement")

        # Test case where replacement text is not found
        mock_get_replacement_text_by_label.return_value = None
        process_labels_in_text(component_manager, entity, base_text)
        mock_set_rendered_text_component.assert_called_with(
            component_manager, entity, base_text)

    @patch('ecs.systems.label_embedding_system.get_replacement_text_by_label')
    @patch('ecs.systems.label_embedding_system.set_instruction')
    @patch('ecs.systems.label_embedding_system.add_linked_label')
    def test_process_labels_in_instruction(self, mock_add_linked_label, mock_set_instruction, mock_get_replacement_text_by_label):
        component_manager = MagicMock(spec=ComponentManager)
        entity = MagicMock(spec=Entity)
        base_text = "This is a :label: instruction."

        # Test case where replacement text is found
        mock_get_replacement_text_by_label.return_value = "replacement"
        process_labels_in_instruction(component_manager, entity, base_text)
        mock_set_instruction.assert_called_with(
            component_manager, entity, "This is a replacement instruction.")
        mock_add_linked_label.assert_called_with(
            component_manager, entity, "label", "replacement")

        # Test case where replacement text is not found
        mock_get_replacement_text_by_label.return_value = None
        process_labels_in_instruction(component_manager, entity, base_text)
        mock_set_instruction.assert_called_with(
            component_manager, entity, base_text)

    @patch('ecs.systems.label_embedding_system.application_state_stable')
    @patch('ecs.systems.label_embedding_system.set_embeddings_changed')
    @patch('ecs.systems.label_embedding_system.reset_text_if_embeddings_changed')
    @patch('ecs.systems.label_embedding_system.process_labels_in_text')
    @patch('ecs.systems.label_embedding_system.process_labels_in_instruction')
    @patch('ecs.systems.label_embedding_system.embeddings_have_changed')
    def test_label_embedding_system_update(self, mock_embeddings_have_changed, mock_process_labels_in_instruction,
                                           mock_process_labels_in_text, mock_reset_text_if_embeddings_changed,
                                           mock_set_embeddings_changed, mock_application_state_stable):
        entity_manager = MagicMock(spec=EntityManager)
        component_manager = MagicMock(spec=ComponentManager)
        system = LabelEmbeddingSystem()

        # Mock application_state_stable to return False so the function proceeds
        mock_application_state_stable.return_value = False

        # Mock entities with TextContentComponent
        entity1 = MagicMock(spec=Entity)
        entity2 = MagicMock(spec=Entity)
        component_manager.get_entities_with_component.side_effect = [
            [entity1, entity2],  # First call for TextContentComponent
            [entity1],           # Second call for InstructionComponent
            [entity1, entity2]   # Third call for ParametersComponent
        ]

        # Mock reset_text_if_embeddings_changed
        mock_reset_text_if_embeddings_changed.return_value = "Base Text"

        # Mock embeddings_have_changed
        mock_embeddings_have_changed.return_value = True

        # Mock get_component for InstructionComponent
        instruction_component_mock = MagicMock()
        instruction_component_mock.instruction = "Instruction Text"
        component_manager.get_component.return_value = instruction_component_mock

        system.update(entity_manager, component_manager)

        # Check calls for TextContentComponent processing
        mock_reset_text_if_embeddings_changed.assert_any_call(
            component_manager, entity1, TextContentComponent)
        mock_reset_text_if_embeddings_changed.assert_any_call(
            component_manager, entity2, TextContentComponent)
        mock_process_labels_in_text.assert_any_call(
            component_manager, entity1, "Base Text")
        mock_process_labels_in_text.assert_any_call(
            component_manager, entity2, "Base Text")

        # Check calls for InstructionComponent processing
        component_manager.get_component.assert_any_call(
            entity1, InstructionComponent)
        mock_process_labels_in_instruction.assert_any_call(
            component_manager, entity1, "Instruction Text")

        # Check that set_embeddings_changed was called
        mock_set_embeddings_changed.assert_called_once_with(
            component_manager, False)


if __name__ == '__main__':
    unittest.main()
