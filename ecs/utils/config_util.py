from ecs.components.config_component import ConfigComponent
from ecs.managers.component_manager import ComponentManager


def get_config(component_manager: ComponentManager, config_key: str) -> str:
    """
    Retrieve the configuration value for a given key from the first entity with a ConfigComponent.

    :param component_manager: Manages entities and their components.
    :param config_key: The key for the configuration value to be retrieved.
    :return: The configuration value associated with the provided key, or None if no entities with ConfigComponent exist.
    """
    config_entities = _retrieve_config_entities(component_manager)

    if _no_entities_with_config(config_entities):
        return None
    else:
        config_entity = _get_first_entity(config_entities)
        config_component = _retrieve_config_component(
            component_manager, config_entity)
        return _get_config_value(config_component, config_key)


def _retrieve_config_entities(component_manager: ComponentManager):
    """
    Retrieve all entities that have a ConfigComponent.

    :param component_manager: Manages entities and their components.
    :return: A list of entities that have a ConfigComponent.
    """
    return component_manager.get_entities_with_component(ConfigComponent)


def _no_entities_with_config(config_entities) -> bool:
    """
    Check if there are no entities with ConfigComponent.

    :param config_entities: List of entities with ConfigComponent.
    :return: True if no entities have ConfigComponent, False otherwise.
    """
    return len(config_entities) == 0


def _get_first_entity(config_entities):
    """
    Get the first entity with ConfigComponent.

    :param config_entities: List of entities with ConfigComponent.
    :return: The first entity with ConfigComponent.
    """
    return next(iter(config_entities))


def _retrieve_config_component(component_manager: ComponentManager, config_entity):
    """
    Retrieve the ConfigComponent from the entity.

    :param component_manager: Manages entities and their components.
    :param config_entity: The entity from which to retrieve the ConfigComponent.
    :return: The ConfigComponent of the entity.
    """
    return component_manager.get_component(config_entity, ConfigComponent)


def _get_config_value(config_component: ConfigComponent, config_key: str) -> str:
    """
    Return the value associated with the config_key from the config_map.

    :param config_component: The ConfigComponent containing the config_map.
    :param config_key: The key for the configuration value to be retrieved.
    :return: The configuration value associated with the provided key.
    """
    return config_component.config_map.get(config_key)
