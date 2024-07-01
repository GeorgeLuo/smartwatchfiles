import os
import re
import shlex
import subprocess
import sys
from typing import List, Tuple
from command_handlers.insert import handle_insert_command
from command_handlers.llm import Model, build_query, call_llm
from ecs.components.command_component import CommandComponent, get_latest_parameter
from ecs.components.instruction_component import InstructionComponent
from ecs.components.rendered_text_component import set_rendered_text_component
from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager
from ecs.utils.config_util import get_config


def get_model(component_manager: ComponentManager, parameters: List[Tuple[str, List[str]]], config_key: str) -> Model:
    config_val = get_latest_parameter(parameters, config_key)
    if config_val:
        return config_val

    config_val = get_config(component_manager, config_key)
    if config_val:
        return config_val

    return None


class LLMCacheValue:
    def __init__(self, response: str, rate_limited: bool):
        self.response = response
        self.rate_limited = rate_limited


class CommandSystem:
    def __init__(self) -> None:
        self.llm_cache = {}

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager):
        entities = component_manager.get_entities_with_component(
            CommandComponent)
        for entity in entities:
            cmd_comp = component_manager.get_component(
                entity, CommandComponent)

            # TODO create command validation logic, do not check just for gen
            if not component_manager.has_component(
                    entity, InstructionComponent) and cmd_comp.command == 'gen':
                set_rendered_text_component(component_manager, entity, '?' + component_manager.get_component(
                    entity, CommandComponent).command)
                continue

            # Check for labels to be embedded
            if component_manager.has_component(entity, InstructionComponent):
                labels = re.findall(r':([\w-]+):', component_manager.get_component(
                    entity, InstructionComponent).render_instruction)
                if labels:
                    set_rendered_text_component(component_manager, entity, component_manager.get_component(
                        entity, InstructionComponent).render_instruction)
                    continue

            match cmd_comp.command:
                case "insert":
                    self._handle_insert(entity, component_manager, cmd_comp)
                case "gen":
                    self._handle_gen(entity, component_manager, cmd_comp)
                case "run":
                    self._handle_run(entity, component_manager, cmd_comp)
                case _:
                    pass

    def _handle_insert(self, entity, component_manager: ComponentManager, cmd_comp: CommandComponent):
        rendered_text = handle_insert_command(cmd_comp.parameters)
        cmd_comp.dirty = False
        set_rendered_text_component(component_manager, entity, rendered_text)

    def _handle_run(self, entity, component_manager: ComponentManager, cmd_comp: CommandComponent):
        instruction_comp = component_manager.get_component(
            entity, InstructionComponent)
        instruction = instruction_comp.render_instruction
        try:
            # Split the instruction into command and arguments
            cmd_parts = shlex.split(instruction)

            # If the command is "python", use the system's Python interpreter
            if cmd_parts[0].lower() == "python":
                cmd_parts[0] = sys.executable

            # Execute the command
            process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False  # It's safer to set shell=False
            )
            # Capture output
            stdout, stderr = process.communicate()
            # Check if the command was successful
            if process.returncode == 0:
                result = f"Command executed successfully.\nOutput:\n{stdout}"
            else:
                result = f"Command failed with return code {process.returncode}.\nError:\n{stderr}"
            # Update the rendered text component with the result
            set_rendered_text_component(component_manager, entity, result)
        except Exception as e:
            error_message = f"An error occurred while executing the command: {str(e)}"
            set_rendered_text_component(
                component_manager, entity, error_message)
        finally:
            # Mark the command as processed
            cmd_comp.dirty = False

    def _handle_gen(self, entity, component_manager: ComponentManager, cmd_comp: CommandComponent):
        instruction_comp = component_manager.get_component(
            entity, InstructionComponent)
        instruction = instruction_comp.render_instruction

        # Check for labels to be embedded, quit early if incomplete instruction
        labels = re.findall(r':([\w-]+):', instruction)
        if labels:
            return
        
        model = get_model(component_manager, cmd_comp.parameters, 'llm')

        query, key = build_query(instruction, cmd_comp.parameters, model)
        cache_value = self.llm_cache.get(key)
        if cache_value and not cache_value.rate_limited:
            rendered_text = cache_value.response
        else:
            # config llm, defer to parameter specifics
            model = get_model(component_manager, cmd_comp.parameters, 'llm')

            rate_limited, rendered_text = call_llm(
                instruction, cmd_comp.parameters, Model(name=model, api_key='your-api-key-here'))
            self.llm_cache[key] = LLMCacheValue(rendered_text, rate_limited)
            # Check for 'write' parameter
            write_params = next(
                (param[1] for param in cmd_comp.parameters if param[0] == 'write'), None)
            if write_params:
                # Pass the first (and only) element of write_params
                self._write_to_file(write_params[0], rendered_text)

        cmd_comp.dirty = False
        set_rendered_text_component(component_manager, entity, rendered_text)

    def _write_to_file(self, file_path: str, content: str):
        try:
            # Split the file_path into directory and filename
            directory = os.path.dirname(file_path)

            # Create directory if it doesn't exist
            if directory:
                os.makedirs(directory, exist_ok=True)

            # Write the content to the file
            with open(file_path, 'w') as file:
                file.write(content)

            print(f"Successfully wrote content to {file_path}")
        except IOError as e:
            print(f"An error occurred while writing to file: {e}")
