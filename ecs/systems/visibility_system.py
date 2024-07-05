from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager


class VisibilitySystem():
    def __init__(self) -> None:
        pass

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager):
        # handle sections with focus labels
        # handle sections with hidden labels
        # handle extraction parameters
        pass