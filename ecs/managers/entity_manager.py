import queue
import threading

from ecs.managers.component_manager import ComponentManager, Entity

MAX_ENTITIES = 1000  # Define a constant for maximum entities


class EntityManager:
    def __init__(self, component_manager: ComponentManager):
        self.available_entities = queue.Queue()
        self.living_entity_count = 0
        self.component_manager = component_manager
        self.mutex = threading.Lock()

        for entity in range(MAX_ENTITIES):
            self.available_entities.put(entity)

    def create_entity(self) -> Entity:
        with self.mutex:
            assert not self.available_entities.empty(), "Too many entities."
            entity_id = self.available_entities.get()
            self.living_entity_count += 1
            return entity_id

    def destroy_entity(self, entity: Entity):
        with self.mutex:
            assert entity < MAX_ENTITIES, "Entity out of range."
            self.component_manager.remove_all_components(entity)
            self.available_entities.put(entity)
            self.living_entity_count -= 1
