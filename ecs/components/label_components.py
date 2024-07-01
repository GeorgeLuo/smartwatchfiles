from ecs.components.rendered_text_component import RenderedTextComponent
from ecs.components.text_content_component import TextContentComponent
from ecs.managers.component_manager import ComponentManager
from typing import Optional, Union, Set, List


def get_replacement_text_by_label(component_manager: ComponentManager, label: str) -> Optional[str]:
    """
    Retrieves the replacement text for a given label from the component manager.

    Args:
        component_manager (ComponentManager): The manager that handles components and entities.
        label (str): The label to search for.

    Returns:
        Optional[str]: The rendered text or text content associated with the label if found, otherwise None.
    """
    # Get all entities with OpeningLabelComponent
    entities = component_manager.get_entities_with_component(
        OpeningLabelComponent)
    for entity in entities:
        opening_label_component = component_manager.get_component(
            entity, OpeningLabelComponent)
        if label in opening_label_component.names:
            # Return the rendered text if available
            if component_manager.has_component(entity, RenderedTextComponent):
                return component_manager.get_component(entity, RenderedTextComponent).rendered_text
            else:
                # Otherwise, return the text content if available
                if component_manager.has_component(entity, TextContentComponent):
                    return component_manager.get_component(entity, TextContentComponent).text_content
                else:
                    return None


class OpeningLabelComponent:
    """
    Component that holds a set of opening label names.

    Attributes:
        names (Set[str]): A set of label names.
    """

    def __init__(self, names: Union[Set[str], List[str], str]):
        if isinstance(names, (set, list)):
            self.names = set(names)
        else:
            self.names = {names}

    def __repr__(self):
        return f"OpeningLabelComponent(names={self.names})"


class ClosingLabelComponent:
    """
    Component that holds a set of closing label names.

    Attributes:
        names (Set[str]): A set of label names.
    """

    def __init__(self, names: Union[Set[str], List[str], str]):
        if isinstance(names, (set, list)):
            self.names = set(names)
        else:
            self.names = {names}

    def __repr__(self):
        return f"ClosingLabelComponent(names={self.names})"
