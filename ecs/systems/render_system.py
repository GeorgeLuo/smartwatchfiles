from typing import Set
from ecs.components.index_component import IndexComponent
from ecs.components.label_components import OpeningLabelComponent
from ecs.components.mark_for_deletion_component import MarkedForDeletionComponent
from ecs.components.rendered_text_component import RenderedTextComponent
from ecs.components.raw_text_component import RawTextComponent
from ecs.components.text_content_component import TextContentComponent
from ecs.managers.component_manager import ComponentManager, Entity
from ecs.managers.entity_manager import EntityManager

def get_in_focus_entities(component_manager: ComponentManager) -> Set[Entity]:

    # get entities labeled with focus
    in_focus = set()

    entities = component_manager.get_entities_with_component(OpeningLabelComponent)
    for entity in entities:
        comp = component_manager.get_component(entity, OpeningLabelComponent)
        if 'focus' in comp.names:
            in_focus.add(entity)

    return in_focus
            
class RenderSystem():

    def __init__(self):
        self.rendered_doc = None
        pass

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager):
        # section_entities = component_manager.get_entities_with_component(
        #     SectionComponent)

        # TODO: not sure why this can't happen earlier
        for entity in component_manager.get_entities_with_component(
            MarkedForDeletionComponent).copy():
            # TODO : move this to pre-render system
            if component_manager.has_component(entity, MarkedForDeletionComponent):
                entity_manager.destroy_entity(entity)

        section_entities = component_manager.get_entities_with_component(
            RawTextComponent).copy()
        
        # sections_map, dirty_found = self.construct_sections_map(
        #     section_entities, entity_manager, component_manager)

        in_focus_entities = get_in_focus_entities(component_manager)
        if len(in_focus_entities) > 0:
            sections_map, dirty_found = self.construct_sections_map_v2(
                in_focus_entities, entity_manager, component_manager)
        else:
            sections_map, dirty_found = self.construct_sections_map_v2(
                section_entities, entity_manager, component_manager)

        if dirty_found:
            rendered_doc = self.render_text(sections_map)
            if self.rendered_doc is None or self.rendered_doc != rendered_doc:
                self.rendered_doc = rendered_doc
                with open('output.txt', 'w') as output_file:
                    output_file.write(rendered_doc)
    
    @staticmethod
    def construct_sections_map_v2(section_entities, entity_manager: EntityManager, component_manager: ComponentManager):
        # Initialize map of integer (index) to section raw_text
        sections_map = {}
        dirty_found = False

        for entity in section_entities:
            # Populate the map

            # TODO : move this to pre-render system
            # if component_manager.has_component(entity, MarkedForDeletionComponent):
            #     dirty_found = True
            #     entity_manager.destroy_entity(entity)
            #     continue
            
            if component_manager.has_component(entity, TextContentComponent):
                text_content = component_manager.get_component(
                    entity, TextContentComponent).text_content
            else:
                text_content = ''
            
            index_component = component_manager.get_component(entity, IndexComponent)

            # TODO : move this too
            if component_manager.has_component(entity, RenderedTextComponent):
                rendered_text_component = component_manager.get_component(
                    entity, RenderedTextComponent)
                sections_map[index_component.index] = rendered_text_component.rendered_text
                dirty_found = rendered_text_component.dirty or dirty_found
                rendered_text_component.dirty = False
            else:
                index_component = component_manager.get_component(entity, IndexComponent)
                sections_map[index_component.index] = text_content
            # if text_content_component.dirty:
            #     dirty_found = True
            # dirty_found = raw_text_component.dirty or dirty_found
            # text_content_component.dirty = False

        return sections_map, True


    def render_text(self, sections_map):
        # Retrieve sections starting from 0 and incrementing until no more found
        complete_text = ''
        index = 0

        # while index in sections_map:
        #     if complete_text:
        #         complete_text += '\n\n'
        #     complete_text += sections_map[index]
        #     index += 1

        index = min(sections_map.keys(), default=None)

        while sections_map:
            if index in sections_map:
                if complete_text:
                    complete_text += '\n\n'
                complete_text += sections_map.pop(index)
            index = min(sections_map.keys(), default=None)

        # Write complete_text to output.txt
        # with open('output.txt', 'w') as output_file:
        #     output_file.write(complete_text)

        return complete_text

# Example usage:
# entity_manager = EntityManager()
# component_manager = ComponentManager()
# render_system = RenderSystem()
# render_system.update(entity_manager, component_manager)
