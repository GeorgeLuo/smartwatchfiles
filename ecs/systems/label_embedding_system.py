import re
from typing import List, Tuple
from ecs.components.command_component import CommandComponent
from ecs.components.instruction_component import InstructionComponent, set_instruction
from ecs.components.linked_entities_by_embedding_component import add_linked_label, embeddings_have_changed
from ecs.components.label_components import get_replacement_text_by_label
from ecs.components.parameters_component import ParametersComponent
from ecs.components.rendered_text_component import RenderedTextComponent, set_rendered_text_component
from ecs.components.text_content_component import TextContentComponent
from ecs.managers.component_manager import ComponentManager, Entity
from ecs.managers.entity_manager import EntityManager

# TODO: something may be wrong with label delete, check behavior in integration


def reset_text_if_embeddings_changed(component_manager: ComponentManager, entity: Entity, component_type: type) -> str:
    """
    Resets the text content if embeddings have changed.

    Args:
        component_manager (ComponentManager): The manager handling components.
        entity (Entity): The entity whose components are being managed.
        component_type (type): The type of the component to reset.

    Returns:
        str: The text content to be used.
    """
    if embeddings_have_changed(component_manager, entity):
        return component_manager.get_component(entity, component_type).text_content
    elif component_manager.has_component(entity, RenderedTextComponent):
        return component_manager.get_component(entity, RenderedTextComponent).rendered_text
    else:
        return component_manager.get_component(entity, component_type).text_content


def process_labels_in_text(component_manager: ComponentManager, entity: Entity, base_text: str) -> None:
    """
    Processes labels in the given text and updates the rendered text component.

    Args:
        component_manager (ComponentManager): The manager handling components.
        entity (Entity): The entity whose components are being managed.
        base_text (str): The base text containing labels to be processed.
    """
    labels = re.findall(r':([\w.-]+):', base_text)
    for label in labels:
        replacement_text = get_replacement_text_by_label(
            component_manager, label)
        if replacement_text is None:
            set_rendered_text_component(component_manager, entity, base_text)
        else:
            base_text = re.sub(rf':{label}:', replacement_text, base_text)
            add_linked_label(component_manager, entity,
                             label, replacement_text)
            set_rendered_text_component(component_manager, entity, base_text)


def process_labels_in_instruction(component_manager: ComponentManager, entity: Entity, base_text: str) -> None:
    """
    Processes labels in the given instruction text and updates the instruction component.

    Args:
        component_manager (ComponentManager): The manager handling components.
        entity (Entity): The entity whose components are being managed.
        base_text (str): The base text containing labels to be processed.
    """
    labels = re.findall(r':([\w.-]+):', base_text)
    for label in labels:
        replacement_text = get_replacement_text_by_label(
            component_manager, label)
        if replacement_text is None:
            # Command should not run at all TODO: figure out what to do, possibly change to a text section
            set_instruction(component_manager, entity, base_text)
        else:
            base_text = re.sub(rf':{label}:', replacement_text, base_text)
            add_linked_label(component_manager, entity,
                             label, replacement_text)
            set_instruction(component_manager, entity, base_text)

def process_labels_in_parameters(component_manager: ComponentManager, entity: Entity, parameters: List[Tuple[str, List[str]]]) -> List[Tuple[str, List[str]]]:
    """
    Processes labels in the given command parameters and updates the command component.

    Args:
        component_manager (ComponentManager): The manager handling components.
        entity (Entity): The entity whose components are being managed.
        parameters (List[Tuple[str, List[str]]]): The command parameters containing labels to be processed.

    Returns:
        List[Tuple[str, List[str]]]: The updated command parameters.
    """
    updated_parameters = []
    for parameter in parameters:
        param_name, param_values = parameter
        updated_values = []
        for parameter_val in param_values:
            labels = re.findall(r':([\w.-]+):', parameter_val)
            for label in labels:
                replacement_text = get_replacement_text_by_label(
                    component_manager, label)
                if replacement_text:
                    parameter_val = re.sub(rf':{label}:', replacement_text, parameter_val)
                    add_linked_label(component_manager, entity, label, replacement_text)
            updated_values.append(parameter_val)
        updated_parameters.append((param_name, updated_values))
    component_manager.get_component(entity, ParametersComponent).render_parameters = updated_parameters

def embeddings_in_parameters_have_changed(component_manager: ComponentManager, entity: Entity):
    
    pass

class LabelEmbeddingSystem():
    """
    System to handle label embedding within text and instruction components.
    """

    def __init__(self) -> None:
        pass

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager) -> None:
        """
        Updates entities by processing label embeddings in their text and instruction components.

        Args:
            entity_manager (EntityManager): The manager handling entities.
            component_manager (ComponentManager): The manager handling components.
        """
        # For entities with TextContentComponents, replace embedded references with the labeled section text
        entities = component_manager.get_entities_with_component(
            TextContentComponent)
        for entity in entities:
            base_text = reset_text_if_embeddings_changed(
                component_manager, entity, TextContentComponent)
            process_labels_in_text(component_manager, entity, base_text)

        # For entities with InstructionComponents, update the instructions with embedded references
        entities = component_manager.get_entities_with_component(
            InstructionComponent)
        for entity in entities:
            if embeddings_have_changed(component_manager, entity):
                base_text = component_manager.get_component(
                    entity, InstructionComponent).instruction
            else:
                base_text = component_manager.get_component(
                    entity, InstructionComponent).render_instruction

            process_labels_in_instruction(component_manager, entity, base_text)

        # For entities with ParametersComponent, update the parameters with embedded references
        entities = component_manager.get_entities_with_component(ParametersComponent)
        for entity in entities:
            parameters_component = component_manager.get_component(entity, ParametersComponent)
            if embeddings_have_changed(component_manager, entity):
                base_parameters = parameters_component.parameters
            else:
                base_parameters = parameters_component.render_parameters


            process_labels_in_parameters(component_manager, entity, base_parameters)
        #     command_component.parameters = updated_parameters
