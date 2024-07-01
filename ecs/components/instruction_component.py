from ecs.managers.component_manager import ComponentManager


def set_instruction(component_manager: ComponentManager, entity, instruction):
    # Set the render_instruction in the InstructionComponent
    component_manager.get_component(entity, InstructionComponent).render_instruction = instruction


class InstructionComponent():
    def __init__(self, instruction: str):
        self.instruction = instruction
        self.render_instruction = instruction