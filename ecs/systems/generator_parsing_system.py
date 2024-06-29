import hashlib
import logging
import threading
from ecs.components.command_component import CommandComponent
from ecs.components.config_component import ConfigComponent
from ecs.components.index_component import IndexComponent
from ecs.components.instruction_component import InstructionComponent
from ecs.components.label_components import ClosingLabelComponent, OpeningLabelComponent
from ecs.components.mark_for_deletion_component import MarkedForDeletionComponent
from ecs.components.raw_text_component import RawTextComponent
from ecs.components.section_type_component import SectionTypeComponent
from ecs.components.text_content_component import TextContentComponent
from ecs.event_bus import EventBus
from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager
from ecs.utils.generator_parser import split_into_sections as gen_split_into_sections
from models.section import parse_section
from ecs.components.dirty_component import DirtyComponent, mark_raw_text_as_dirty

# The watcher system handles file change events and parses the file into
# sections, then parses out the sections SectionComponent metadata,
# and detects changes.

# The metadata: raw_text, labels, commands, instructions, and parameters

# This may seem like a lot of responsibility, but there is not much variation
# in how the sections can appear. The syntax will remain the same, and
# all features derive from the boundaries of the syntax.

# TODO: handle changes to config_entities

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def compute_hash(file_path: str) -> str:
    """
    Compute the MD5 hash of the file at the given path.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The computed MD5 hash of the file.
    """
    hasher = hashlib.md5()
    with open(file_path, 'rb') as file:
        buf = file.read()
        hasher.update(buf)
    return hasher.hexdigest()


def construct_sections_map(section_entities: list, component_manager: ComponentManager) -> tuple:
    """
    Construct a map of sections based on their raw text and check if any are dirty.

    Args:
        section_entities (list): List of section entities.
        component_manager (ComponentManager): The component manager to manage components.

    Returns:
        tuple: A tuple containing the sections map and a boolean indicating if any section is dirty.
    """
    sections_map = {}
    dirty_found = False

    for entity in section_entities:
        section_component = component_manager.get_component(
            entity, RawTextComponent)
        if section_component.raw_string not in sections_map:
            sections_map[section_component.raw_string] = []
        sections_map[section_component.raw_string].append(
            (entity, section_component))
        dirty_found = section_component.dirty or dirty_found
        section_component.dirty = False

    return sections_map, dirty_found


def parse_config_sections(config_sections: list) -> dict:
    """
    Parse configuration sections into a configuration map.

    Args:
        config_sections (list): List of configuration sections.

    Returns:
        dict: A dictionary containing configuration key-value pairs.
    """
    config_map = {}
    for section in config_sections:
        lines = section['raw_text'].strip().split('\n')
        for line in lines:
            if line.startswith('!'):
                key_value = line[1:].split('=', 1)
                if len(key_value) == 2:
                    key, value = key_value
                    config_map[key.strip()] = value.strip()
    return config_map


def process_sections(sections_data: list, known_sections_map: dict, entity_manager: EntityManager, component_manager: ComponentManager, version_hash: str):
    """
    Process sections and update or create entities based on the sections data.

    Args:
        sections_data (list): List of parsed sections data.
        known_sections_map (dict): Map of known sections.
        entity_manager (EntityManager): The entity manager to manage entities.
        component_manager (ComponentManager): The component manager to manage components.
        version_hash (str): The version hash of the file.
    """
    for index, section in enumerate(sections_data):
        if section.raw_text not in known_sections_map:
            new_entity = entity_manager.create_entity()
            component_manager.add_component(new_entity, RawTextComponent(
                index, section.raw_text, version_hash))
            component_manager.add_component(new_entity, IndexComponent(index))
            component_manager.add_component(
                new_entity, SectionTypeComponent(section.section_type))
            if section.text_content is not None:
                component_manager.add_component(
                    new_entity, TextContentComponent(section.text_content))
            if section.command is not None:
                component_manager.add_component(
                    new_entity, CommandComponent(section.command, section.parameters))
            if section.instruction is not None:
                component_manager.add_component(
                    new_entity, InstructionComponent(section.instruction))
            if len(section.opening_labels) > 0:
                component_manager.add_component(
                    new_entity, OpeningLabelComponent(section.opening_labels))
            if len(section.closing_labels) > 0:
                component_manager.add_component(
                    new_entity, ClosingLabelComponent(section.closing_labels))
        else:
            entity, raw_text_component = known_sections_map[section.raw_text].pop(
                0)
            if not known_sections_map[section.raw_text]:
                del known_sections_map[section.raw_text]

            index_component = component_manager.get_component(
                entity, IndexComponent)
            if index_component.index != index:
                index_component.index = index
                raw_text_component.dirty = True
                mark_raw_text_as_dirty(entity, component_manager)


def mark_remaining_sections_for_deletion(known_sections_map: dict, component_manager: ComponentManager):
    """
    Mark remaining sections for deletion.

    Args:
        known_sections_map (dict): Map of known sections.
        component_manager (ComponentManager): The component manager to manage components.
    """
    for sections in known_sections_map.values():
        for entity in sections:
            if component_manager.has_component(entity[0], MarkedForDeletionComponent):
                thread_id = threading.get_ident()
                logging.warning(
                    f"Duplicate MarkedForDeletionComponent found for entity {entity[0]} in thread {thread_id}")
            else:
                new_component = MarkedForDeletionComponent()
                component_manager.add_component(entity[0], new_component)


def handle_config_entities(config_map: dict, entity_manager: EntityManager, component_manager: ComponentManager):
    """
    Handle configuration entities by updating or creating them based on the configuration map.

    Args:
        config_map (dict): The configuration map containing key-value pairs.
        entity_manager (EntityManager): The entity manager to manage entities.
        component_manager (ComponentManager): The component manager to manage components.
    """
    config_entities = component_manager.get_entities_with_component(
        ConfigComponent)
    if len(config_entities) == 0:
        config_entity = entity_manager.create_entity()
        component_manager.add_component(
            config_entity, ConfigComponent(config_map))
    else:
        config_entity = next(iter(config_entities))
        config_component = component_manager.get_component(
            config_entity, ConfigComponent)
        for key, value in config_map.items():
            config_component.config_map[key] = value


class GeneratorParsingSystem():

    def __init__(self, event_bus: EventBus):
        """
        Initialize the GeneratorParsingSystem with an event bus.

        Args:
            event_bus (EventBus): The event bus to handle events.
        """
        self.event_bus = event_bus

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager):
        """
        Update the system by processing events from the event bus.

        Args:
            entity_manager (EntityManager): The entity manager to manage entities.
            component_manager (ComponentManager): The component manager to manage components.
        """
        events = self.event_bus.get_events()
        for event_type, event_data in events:
            if event_type == "file_modified":
                # Handle file modified event
                self.handle_file_modified_v2(
                    event_data, entity_manager, component_manager)

    def handle_file_modified_v2(self, event_data: dict, entity_manager: EntityManager, component_manager: ComponentManager):
        """
        Handle the file modified event by processing the file and updating entities.

        Args:
            event_data (dict): The event data containing file information.
            entity_manager (EntityManager): The entity manager to manage entities.
            component_manager (ComponentManager): The component manager to manage components.
        """
        print(f"File modified: {event_data['file_name']}")

        # Read the file content
        with open(event_data['file_name'], 'r') as generator_file:
            content = generator_file.readlines()

        # Compute the hash of the file
        version_hash = compute_hash(event_data['file_name'])

        # Remove all lines that start with a hashtag
        content = ''.join(
            [line for line in content if not line.strip().startswith('#')])

        # Split content into sections
        generator_sections = gen_split_into_sections(content)

        # Extract and remove config sections
        config_sections = [
            section for section in generator_sections if section['raw_text'].strip().startswith('!')]
        non_config_sections = [
            section for section in generator_sections if not section['raw_text'].strip().startswith('!')]

        # Parse config sections into a config map
        config_map = parse_config_sections(config_sections)

        # Handle config entities
        # TODO we may have multiple config sets in the future, ie imported config collections
        handle_config_entities(config_map, entity_manager, component_manager)

        # Parse non-config sections
        sections_data = [parse_section(section['raw_text'])
                         for section in non_config_sections]

        # Map sections to entities
        section_entities = component_manager.get_entities_with_component(
            RawTextComponent)
        known_sections_map, _ = construct_sections_map(
            section_entities, component_manager)

        # Process sections
        process_sections(sections_data, known_sections_map,
                         entity_manager, component_manager, version_hash)

        # Mark remaining sections for deletion
        mark_remaining_sections_for_deletion(
            known_sections_map, component_manager)
