from ecs.managers.component_manager import ComponentManager, Entity


def set_rendered_text_component(component_manager: ComponentManager, entity: Entity, rendered_text: str) -> None:
    """
    Sets the rendered text for a given entity. If the entity does not already have a RenderedTextComponent,
    it adds one.

    Args:
        component_manager (ComponentManager): Manages components for entities.
        entity (Entity): The entity to which the rendered text component is to be set.
        rendered_text (str): The text to be rendered.

    Returns:
        None
    """
    if component_manager.has_component(entity, RenderedTextComponent):
        component_manager.get_component(
            entity, RenderedTextComponent).rendered_text = rendered_text
    else:
        component_manager.add_component(
            entity, RenderedTextComponent(rendered_text))


class RenderedTextComponent:
    """
    A component that holds rendered text.

    Attributes:
        rendered_text (str): The text that has been rendered.
    """

    def __init__(self, rendered_text: str) -> None:
        """
        Initializes the RenderedTextComponent with the given rendered text.

        Args:
            rendered_text (str): The text to be rendered.
        """
        self.rendered_text = rendered_text