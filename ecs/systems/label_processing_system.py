from typing import Any, Type
from ecs.components.visibility_component import HiddenComponent, InFocusComponent
from ecs.components.label_components import OpeningLabelComponent
from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager


def upsert_component(component_manager: ComponentManager, entity: int, component_cls: Type[Any]):
    """
    Upserts a component for an entity. If the component already exists, it does nothing.
    If the component does not exist, it adds the component to the entity.

    Args:
        component_manager (ComponentManager): The component manager instance.
        entity (Entity): The entity to upsert the component for.
        component_cls (Type[Component]): The class of the component to upsert.
    """
    if not component_manager.has_component(entity, component_cls):
        component_instance = component_cls()  # Initialize the component
        component_manager.add_component(entity, component_instance)


class LabelProcessingSystem:
    def __init__(self) -> None:
        pass

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager):
        # find focus labels and create components for these sections
        entities = component_manager.get_entities_with_component(
            OpeningLabelComponent)
        for entity in entities:
            opening_comp = component_manager.get_component(
                entity, OpeningLabelComponent)
            if 'focus' in opening_comp.names:
                upsert_component(component_manager, entity, InFocusComponent)

        # find hidden labels and create components for these sections
        for entity in entities:
            opening_comp = component_manager.get_component(
                entity, OpeningLabelComponent)
            if 'hidden' in opening_comp.names:
                upsert_component(component_manager, entity, HiddenComponent)
