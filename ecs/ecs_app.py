from ecs.event_bus import EventBus
from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager


class ECSApp:
    def __init__(self):
        self.event_bus = EventBus()
        self.component_manager = ComponentManager()
        self.entity_manager = EntityManager(self.component_manager)
        self.systems = []

    def add_system(self, system):
        self.systems.append(system)

    def update_systems(self):
        for system in self.systems:
            system.update(self.entity_manager, self.component_manager)

    def run(self):
        while True:
            self.update_systems()
