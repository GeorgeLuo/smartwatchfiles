from typing import Dict, Optional

from ecs.components.label_components import get_replacement_text_by_label
from ecs.managers.component_manager import ComponentManager, Entity


def add_linked_label(component_manager: ComponentManager, entity: Entity, label: str, replacement_text: str):
    # Add or update the linked label in the LinkedLabelsToTextComponent
    if component_manager.has_component(entity, LinkedLabelsToTextComponent):
        component_manager.get_component(
            entity, LinkedLabelsToTextComponent).add_link(label, replacement_text)
    else:
        component_manager.add_component(
            entity, LinkedLabelsToTextComponent(label, replacement_text))


def embeddings_have_changed(component_manager: ComponentManager, entity: Entity) -> bool:
    """
    Check if any of the linked embeddings for an entity have changed.
    This function examines the LinkedLabelsToTextComponent of the given entity
    and compares the stored linked text for each label with the current text
    associated with that label in the component manager.

    Args:
        component_manager (ComponentManager): The component manager containing
            entity components.
        entity (Entity): The entity to check for embedding changes.

    Returns:
        bool: True if any linked embedding has changed, False otherwise.

    Note:
        This function assumes the existence of a LinkedLabelsToTextComponent
        and a method get_replacement_text_by_label() to retrieve current text
        for a given label.
    """
    if component_manager.has_component(entity, LinkedLabelsToTextComponent):
        linked_entities_by_embeddings = component_manager.get_component(
            entity, LinkedLabelsToTextComponent)
        for linked_label, linked_text in linked_entities_by_embeddings.linked_labels.items():
            current_linked_text = get_replacement_text_by_label(
                component_manager, linked_label)
            if linked_text != current_linked_text:
                return True
    return False


class LinkedLabelsToTextComponent:
    def __init__(self, label: Optional[str] = None, replacement_text: Optional[str] = None):
        self.linked_labels: Dict[str, str] = {}
        if label is not None and replacement_text is not None:
            self.add_link(label, replacement_text)

    def add_link(self, label: str, replacement_text: str):
        self.linked_labels[label] = replacement_text

    def __repr__(self):
        return f"LinkedLabelsToTextComponent(linked_labels={self.linked_labels})"
