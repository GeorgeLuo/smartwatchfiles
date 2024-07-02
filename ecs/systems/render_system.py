from typing import Set, Dict
from ecs.components.index_component import IndexComponent
from ecs.components.label_components import OpeningLabelComponent
from ecs.components.mark_for_deletion_component import MarkedForDeletionComponent
from ecs.components.rendered_text_component import RenderedTextComponent
from ecs.components.raw_text_component import RawTextComponent
from ecs.components.text_content_component import TextContentComponent
from ecs.managers.component_manager import ComponentManager, Entity
from ecs.managers.entity_manager import EntityManager

def get_in_focus_entities(component_manager: ComponentManager) -> Set[Entity]:
    """
    Get entities labeled with focus.

    Business Logic:
    - This function retrieves all entities that have the `OpeningLabelComponent` and checks if they are labeled with 'focus'.
    - Entities with the 'focus' label are added to the `in_focus` set.

    Args:
        component_manager (ComponentManager): The component manager to manage components.

    Returns:
        Set[Entity]: of entities that are in focus.
    """
    in_focus = set()

    entities = component_manager.get_entities_with_component(
        OpeningLabelComponent)
    for entity in entities:
        comp = component_manager.get_component(entity, OpeningLabelComponent)
        if 'focus' in comp.names:
            in_focus.add(entity)

    return in_focus


def handle_marked_for_deletion_entities(entity_manager: EntityManager, component_manager: ComponentManager):
    """
    Handle entities marked for deletion.

    Business Logic:
    - This function iterates over entities that have the `MarkedForDeletionComponent` and destroys them using the `entity_manager`.

    Args:
        entity_manager (EntityManager): EntityManager
        component_manager (ComponentManager): ComponentManager
    """
    # TODO: not sure why this can't happen earlier
    for entity in component_manager.get_entities_with_component(
            MarkedForDeletionComponent).copy():
        # TODO : move this to pre-render system
        if component_manager.has_component(entity, MarkedForDeletionComponent):
            entity_manager.destroy_entity(entity)


def construct_sections_map(section_entities: Set[Entity], entity_manager: EntityManager, component_manager: ComponentManager) -> Dict[int, str]:
    """
    Construct a map of section indices to their corresponding text content.

    Business Logic:
    - This function creates a dictionary mapping indices to text content for given entities.
    - If an entity has a `RenderedTextComponent`, its rendered text is used.
    - Otherwise, the raw text content is used.

    Args:
        section_entities: Set of entities to process
        entity_manager: EntityManager
        component_manager: ComponentManager

    Returns:
        Dict[int, str]: mapping of indices to text content.
    """
    sections_map = {}

    for entity in section_entities:
        # Get text content if available
        if component_manager.has_component(entity, TextContentComponent):
            text_content = component_manager.get_component(
                entity, TextContentComponent).text_content
        else:
            text_content = ''

        index_component = component_manager.get_component(
            entity, IndexComponent)

        # Check if entity has rendered text component
        # TODO : move this too
        if component_manager.has_component(entity, RenderedTextComponent):
            rendered_text_component = component_manager.get_component(
                entity, RenderedTextComponent)
            sections_map[index_component.index] = rendered_text_component.rendered_text
        else:
            index_component = component_manager.get_component(
                entity, IndexComponent)
            sections_map[index_component.index] = text_content
    return sections_map


def render_text(sections_map: Dict[int, str]) -> str:
    """
    Render the complete text from sections map.

    Business Logic:
    - This function concatenates text sections in order of their indices.
    - Sections are separated by double newlines.

    Args:
        sections_map: Dictionary mapping indices to text content

    Returns:
        str: Complete rendered text as a single string.
    """
    complete_text = ''
    index = 0

    # Get the minimum index to start with
    index = min(sections_map.keys(), default=None)

    while sections_map:
        if index in sections_map:
            if complete_text:
                complete_text += '\n\n'
            complete_text += sections_map.pop(index)
        # Update index to the next minimum key
        index = min(sections_map.keys(), default=None)

    return complete_text


class RenderSystem():
    """
    RenderSystem class responsible for updating and rendering text content.

    Business Logic:
    - This class handles the update cycle for rendering text.
    - It processes entities marked for deletion, constructs a sections map, and renders the text.
    - The rendered text is written to a file if it has changed.

    Methods:
    - __init__: Initializes the RenderSystem.
    - update: Updates the system by processing entities and rendering text.
    """

    def __init__(self, generated_file):
        self.rendered_doc = None
        self.generated_file = generated_file
        pass

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager):
        """
        Update the RenderSystem.

        Business Logic:
        - Handles entities marked for deletion.
        - Constructs a sections map from either in-focus entities or all entities with raw text components.
        - Renders the text and writes it to a file if it has changed.

        Args:
            entity_manager: EntityManager
            component_manager: ComponentManager
        """
        handle_marked_for_deletion_entities(entity_manager, component_manager)

        # Get entities with raw text components
        section_entities = component_manager.get_entities_with_component(
            RawTextComponent).copy()

        # Get entities that are in focus
        in_focus_entities = get_in_focus_entities(component_manager)
        if len(in_focus_entities) > 0:
            sections_map = construct_sections_map(
                in_focus_entities, entity_manager, component_manager)
        else:
            sections_map = construct_sections_map(
                section_entities, entity_manager, component_manager)

        # Render the text and write to file if it has changed
        rendered_doc = render_text(sections_map)
        if self.rendered_doc is None or self.rendered_doc != rendered_doc:
            self.rendered_doc = rendered_doc
            with open(self.generated_file, 'w') as output_file:
                output_file.write(rendered_doc)