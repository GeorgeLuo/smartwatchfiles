from ecs.managers.component_manager import ComponentManager
from typing import Optional


class ApplicationMetadataComponent:
    def __init__(self) -> None:
        self.render_stable = False
        self.embeddings_stable = False


def get_application_metadata(component_manager: ComponentManager) -> Optional[ApplicationMetadataComponent]:
    """
    Retrieve the ApplicationMetadataComponent from the component manager.

    Args:
        component_manager (ComponentManager): The component manager instance.

    Returns:
        ApplicationMetadataComponent: The ApplicationMetadataComponent if it exists, otherwise None.
    """
    application_metadata_entities = component_manager.get_entities_with_component(
        ApplicationMetadataComponent)
    if not application_metadata_entities:
        return None

    metadata_entity = next(iter(application_metadata_entities))
    return component_manager.get_component(metadata_entity, ApplicationMetadataComponent)


def application_state_stable(component_manager: ComponentManager) -> bool:
    application_metadata = get_application_metadata(component_manager)
    if application_metadata is None:
        return False
    return application_metadata.render_stable and application_metadata.embeddings_stable


def changes_made(component_manager: ComponentManager):
    application_metadata = get_application_metadata(component_manager)
    if application_metadata is not None:
        application_metadata.render_stable = False


def set_embeddings_changed(component_manager: ComponentManager, val: bool):
    application_metadata = get_application_metadata(component_manager)
    if application_metadata is not None:
        application_metadata.embeddings_stable = val
