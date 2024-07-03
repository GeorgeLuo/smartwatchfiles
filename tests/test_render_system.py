import unittest
from unittest.mock import MagicMock, patch
from ecs.systems.render_system import (
    get_in_focus_entities,
    handle_marked_for_deletion_entities,
    construct_sections_map,
    render_text,
    RenderSystem
)
from ecs.components.index_component import IndexComponent
from ecs.components.label_components import OpeningLabelComponent
from ecs.components.mark_for_deletion_component import MarkedForDeletionComponent
from ecs.components.rendered_text_component import RenderedTextComponent
from ecs.components.raw_text_component import RawTextComponent
from ecs.components.text_content_component import TextContentComponent
from ecs.managers.component_manager import ComponentManager, Entity
from ecs.managers.entity_manager import EntityManager


class TestRenderSystem(unittest.TestCase):

    def setUp(self):
        self.component_manager = MagicMock(spec=ComponentManager)
        self.entity_manager = MagicMock(spec=EntityManager)

    def test_get_in_focus_entities(self):
        entity1 = Entity(1)
        entity2 = Entity(2)
        self.component_manager.get_entities_with_component.return_value = {
            entity1, entity2}
        self.component_manager.get_component.side_effect = lambda e, c: OpeningLabelComponent(
            names=['focus']) if e == entity1 else OpeningLabelComponent(names=[])

        result = get_in_focus_entities(self.component_manager)
        self.assertEqual(result, {entity1})

    def test_handle_marked_for_deletion_entities(self):
        entity1 = Entity(1)
        entity2 = Entity(2)
        self.component_manager.get_entities_with_component.return_value = {
            entity1, entity2}
        self.component_manager.has_component.side_effect = lambda e, c: True

        handle_marked_for_deletion_entities(
            self.entity_manager, self.component_manager)
        self.entity_manager.destroy_entity.assert_any_call(entity1)
        self.entity_manager.destroy_entity.assert_any_call(entity2)

    def test_construct_sections_map(self):
        entity1 = Entity(1)
        entity2 = Entity(2)

        # Define the side_effect for get_component to return the appropriate component based on the entity and component class
        def get_component_side_effect(entity, component_cls):
            if component_cls == IndexComponent:
                return IndexComponent(index=1) if entity == entity1 else IndexComponent(index=2)
            elif component_cls == TextContentComponent:
                return TextContentComponent(text_content="Text 1") if entity == entity1 else TextContentComponent(text_content="Text 2")
            elif component_cls == RenderedTextComponent:
                return RenderedTextComponent(rendered_text="Rendered Text 2") if entity == entity2 else None
            return None

        self.component_manager.get_component.side_effect = get_component_side_effect

        # Define the side_effect for has_component
        self.component_manager.has_component.side_effect = lambda e, c: (
            (c == TextContentComponent and e in [entity1, entity2]) or
            (c == RenderedTextComponent and e == entity2)
        )

        result = construct_sections_map(
            {entity1, entity2}, self.entity_manager, self.component_manager)
        self.assertEqual(result, {1: "Text 1", 2: "Rendered Text 2"})

    def test_render_text(self):
        sections_map = {1: "Section 1", 2: "Section 2", 3: "Section 3"}
        result = render_text(sections_map)
        self.assertEqual(result, "Section 1\n\nSection 2\n\nSection 3")

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_render_system_update(self, mock_open):
        render_system = RenderSystem('output.txt')
        entity1 = Entity(1)
        entity2 = Entity(2)

        # Define the side_effect for get_entities_with_component
        self.component_manager.get_entities_with_component.side_effect = lambda c: {
            entity1, entity2} if c == RawTextComponent else set()

        # Define the side_effect for get_component to return the appropriate component based on the entity and component class
        def get_component_side_effect(entity, component_cls):
            if component_cls == IndexComponent:
                return IndexComponent(index=1) if entity == entity1 else IndexComponent(index=2)
            elif component_cls == TextContentComponent:
                return TextContentComponent(text_content="Text 1") if entity == entity1 else TextContentComponent(text_content="Text 2")
            return None

        self.component_manager.get_component.side_effect = get_component_side_effect

        # Define the side_effect for has_component
        self.component_manager.has_component.side_effect = lambda e, c: c == TextContentComponent

        render_system.update(self.entity_manager, self.component_manager)
        mock_open.assert_called_once_with('output.txt', 'w')
        mock_open().write.assert_called_once_with("Text 1\n\nText 2")


if __name__ == '__main__':
    unittest.main()
