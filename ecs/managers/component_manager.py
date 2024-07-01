import threading
from typing import Any, Dict, Type, Set

from typing import TypeVar, Type

T = TypeVar('T')


# Constants
MAX_ENTITIES = 1000
INVALID_ENTITY = -1

# Entity is just an int in this simplified ECS
Entity = int


class IComponentArray:
    def remove_component_if_exists(self, entity: Entity):
        raise NotImplementedError


class ComponentArray(IComponentArray):
    def __init__(self, component_type: Type[Any]):
        self.component_storage = [None] * MAX_ENTITIES
        self.entity_to_component_mapping = [False] * MAX_ENTITIES
        self.component_count = 0
        self.component_type = component_type

    def add_component(self, entity: Entity, component: Any):
        assert entity < MAX_ENTITIES, "Entity ID out of range."
        assert not self.entity_to_component_mapping[entity], "Component already exists for entity."

        self.component_storage[entity] = component
        self.entity_to_component_mapping[entity] = True
        self.component_count += 1

    def remove_component(self, entity: Entity):
        assert entity < MAX_ENTITIES, "Entity ID out of range."
        assert self.entity_to_component_mapping[entity], "Removing non-existent component."

        self.entity_to_component_mapping[entity] = False
        self.component_storage[entity] = None
        self.component_count -= 1

    def remove_component_if_exists(self, entity: Entity):
        if entity < MAX_ENTITIES and self.entity_to_component_mapping[entity]:
            self.entity_to_component_mapping[entity] = False
            self.component_storage[entity] = None
            self.component_count -= 1

    def get_component(self, entity: Entity):
        assert entity < MAX_ENTITIES, "Entity ID out of range."
        assert self.entity_to_component_mapping[entity], "Component does not exist for entity."

        return self.component_storage[entity]

    def has_component(self, entity: Entity):
        assert entity < MAX_ENTITIES, "Entity ID out of range."
        return self.entity_to_component_mapping[entity]


class ComponentManager:
    def __init__(self):
        self.component_arrays: Dict[Type[Any], ComponentArray] = {}
        self.entities_by_component_type: Dict[Type[Any], Set[Entity]] = {}
        self.valid_entities: Set[Entity] = set()
        self.mutex = threading.Lock()

    def get_component_array(self, component_type: Type[Any]) -> ComponentArray:
        if component_type not in self.component_arrays:
            self.component_arrays[component_type] = ComponentArray(
                component_type)
        return self.component_arrays[component_type]

    def add_component(self, entity: Entity, component: Any):
        with self.mutex:
            component_type = type(component)
            component_array = self.get_component_array(component_type)
            component_array.add_component(entity, component)
            if component_type not in self.entities_by_component_type:
                self.entities_by_component_type[component_type] = set()
            self.entities_by_component_type[component_type].add(entity)
            self.valid_entities.add(entity)

    def has_component(self, entity: Entity, component_type: Type[Any]) -> bool:
        with self.mutex:
            component_array = self.get_component_array(component_type)
            return component_array.has_component(entity)

    def get_component(self, entity: Entity, component_type: Type[T]) -> T:
        with self.mutex:
            component_array = self.get_component_array(component_type)
            return component_array.get_component(entity)

    def remove_component(self, entity: Entity, component_type: Type[Any]):
        with self.mutex:
            component_array = self.get_component_array(component_type)
            component_array.remove_component(entity)
            self.entities_by_component_type[component_type].discard(entity)
            if all(not array.has_component(entity) for array in self.component_arrays.values()):
                self.valid_entities.discard(entity)

    def remove_all_components(self, entity: Entity):
        with self.mutex:
            for component_array in self.component_arrays.values():
                component_array.remove_component_if_exists(entity)
            for entities in self.entities_by_component_type.values():
                entities.discard(entity)
            self.valid_entities.discard(entity)

    def is_valid_entity(self, entity: Entity) -> bool:
        with self.mutex:
            return entity in self.valid_entities

    def get_entities_with_component(self, component_type: Type[Any]) -> Set[Entity]:
        with self.mutex:
            return self.entities_by_component_type.get(component_type, set())

    def get_entities_with_components(self, *component_types: Type[Any]) -> Set[Entity]:
        with self.mutex:
            if not component_types:
                return set()
            result = self.entities_by_component_type.get(
                component_types[0], set()).copy()
            for component_type in component_types[1:]:
                result.intersection_update(
                    self.entities_by_component_type.get(component_type, set()))
            return result
