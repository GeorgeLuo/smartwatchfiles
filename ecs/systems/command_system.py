import os
import re
import shlex
import subprocess
import sys
from typing import List, Optional, Tuple
from command_handlers.insert import handle_insert_command
from command_handlers.llm import Model, build_query, call_llm
from ecs.components.command_component import CommandComponent, get_latest_parameter
from ecs.components.instruction_component import InstructionComponent
from ecs.components.parameters_component import ParametersComponent
from ecs.components.rendered_text_component import set_rendered_text_component
from ecs.managers.component_manager import ComponentManager
from ecs.managers.entity_manager import EntityManager
from ecs.utils.config_util import get_config


def get_model(component_manager: ComponentManager, parameters: List[Tuple[str, List[str]]]) -> Optional[Model]:
    """
    Retrieve the latest parameter value for the given config key and "llm-api-key". 
    If not found, get the config value from the component manager.

    Args:
        component_manager (ComponentManager): The component manager instance.
        parameters (List[Tuple[str, List[str]]]): List of parameters.
        config_key (str): The configuration key to look up.

    Returns:
        Optional[Model]: The model configuration, or None if not found.
    """
    
    def get_latest_or_config(key: str) -> Optional[str]:
        # Function to retrieve the latest parameter value or config value
        val = get_latest_parameter(parameters, key)
        if not val:
            val = get_config(component_manager, key)
        return val
    
    # Retrieve the llm name
    llm_name = get_latest_or_config("llm")
    # Retrieve the llm-api-key
    llm_api_key = get_latest_or_config("llm-api-key")
    
    if llm_name and llm_api_key:
        return Model(name=llm_name, api_key=llm_api_key)
    
    return None


def handle_insert(entity, component_manager: ComponentManager, parameters_component: ParametersComponent):
    """
    Handle the 'insert' command by processing the parameters and updating the rendered text component.

    Args:
        entity: The entity to which the command belongs.
        component_manager (ComponentManager): The component manager instance.
        cmd_comp (CommandComponent): The command component containing the command details.
    """
    rendered_text = handle_insert_command(parameters_component.render_parameters)
    set_rendered_text_component(component_manager, entity, rendered_text)


def handle_run(entity, component_manager: ComponentManager, cmd_comp: CommandComponent):
    """
    Handle the 'run' command by executing the instruction as a system command and updating the rendered text component with the result.

    Args:
        entity: The entity to which the command belongs.
        component_manager (ComponentManager): The component manager instance.
        cmd_comp (CommandComponent): The command component containing the command details.
    """
    instruction_comp = component_manager.get_component(
        entity, InstructionComponent)
    instruction = instruction_comp.render_instruction
    try:
        cmd_parts = shlex.split(instruction)
        if cmd_parts[0].lower() == "python":
            cmd_parts[0] = sys.executable

        process = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            result = f"Command executed successfully.\nOutput:\n{stdout}"
        else:
            result = f"Command failed with return code {process.returncode}.\nError:\n{stderr}"
        set_rendered_text_component(component_manager, entity, result)
    except Exception as e:
        error_message = f"An error occurred while executing the command: {str(e)}"
        set_rendered_text_component(component_manager, entity, error_message)


def handle_gen(entity, component_manager: ComponentManager, llm_cache: dict):
    """
    Handle the 'gen' command by generating text using a language model and updating the rendered text component.

    Args:
        entity: The entity to which the command belongs.
        component_manager (ComponentManager): The component manager instance.
        llm_cache (dict): Cache for language model responses.
    """
    instruction_comp = component_manager.get_component(
        entity, InstructionComponent)
    instruction = instruction_comp.render_instruction

    parameters_comp = component_manager.get_component(
        entity, ParametersComponent)
    parameters = parameters_comp.render_parameters

    labels = re.findall(r':([\w-]+):', instruction)
    if labels:
        return

    model = get_model(component_manager, parameters)

    query, query_key = build_query(instruction, parameters, model.name)
    cache_value = llm_cache.get(query_key)
    if cache_value and not cache_value.rate_limited:
        rendered_text = cache_value.response
    else:
        rate_limited, rendered_text = call_llm(
            instruction, parameters, model)
        
        if rate_limited:
            pass

        llm_cache[query_key] = LLMCacheValue(rendered_text, rate_limited)
        write_params = next(
            (param[1] for param in parameters if param[0] == 'write'), None)
        if write_params:
            write_to_file(write_params[0], rendered_text)

    set_rendered_text_component(component_manager, entity, rendered_text)


def write_to_file(file_path: str, content: str):
    """
    Write the given content to a file at the specified file path.

    Args:
        file_path (str): The path to the file.
        content (str): The content to write to the file.
    """
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, 'w') as file:
            file.write(content)

        print(f"Successfully wrote content to {file_path}")
    except IOError as e:
        print(f"An error occurred while writing to file: {e}")


class LLMCacheValue:
    """
    A class to represent the cache value for language model responses.

    Attributes:
        response (str): The response from the language model.
        rate_limited (bool): Whether the response was rate-limited.
    """

    def __init__(self, response: str, rate_limited: bool):
        self.response = response
        self.rate_limited = rate_limited


class CommandSystem:
    """
    The CommandSystem class is responsible for processing commands for entities.

    Attributes:
        llm_cache (dict): Cache for language model responses.
    """

    def __init__(self) -> None:
        self.llm_cache = {}

    def update(self, entity_manager: EntityManager, component_manager: ComponentManager):
        """
        Update the command system by processing commands for all entities with a CommandComponent.

        Args:
            entity_manager (EntityManager): The entity manager instance.
            component_manager (ComponentManager): The component manager instance.
        """
        entities = component_manager.get_entities_with_component(
            CommandComponent)
        for entity in entities:
            cmd_comp = component_manager.get_component(
                entity, CommandComponent)

            # TODO create command validation logic, do not check just for gen
            if not component_manager.has_component(entity, InstructionComponent) and cmd_comp.command == 'gen':
                set_rendered_text_component(
                    component_manager, entity, '?' + component_manager.get_component(entity, CommandComponent).command)
                continue

            if component_manager.has_component(entity, InstructionComponent):
                labels = re.findall(r':([\w-]+):', component_manager.get_component(
                    entity, InstructionComponent).render_instruction)
                if labels:
                    set_rendered_text_component(component_manager, entity, component_manager.get_component(
                        entity, InstructionComponent).render_instruction)
                    continue

            if component_manager.has_component(entity, ParametersComponent):
                
                parameters = component_manager.get_component(
                    entity, ParametersComponent).render_parameters
                
                has_unpopulated_embedding_in_parameters = False
                for parameter in parameters:
                    for parameter_val in parameter[1]:
                        labels = re.findall(r':([\w-]+):', parameter_val)
                        if labels:
                            set_rendered_text_component(
                                component_manager, entity, '?' + component_manager.get_component(entity, CommandComponent).command)
                            has_unpopulated_embedding_in_parameters = True
                            break
                        if has_unpopulated_embedding_in_parameters:
                            break
                    if has_unpopulated_embedding_in_parameters:
                        break
                if has_unpopulated_embedding_in_parameters:
                    continue

            match cmd_comp.command:
                case "insert":
                    parameters = component_manager.get_component(entity, ParametersComponent)
                    handle_insert(entity, component_manager, parameters)
                case "gen":
                    handle_gen(entity, component_manager, self.llm_cache)
                case "run":
                    handle_run(entity, component_manager, cmd_comp)
                case _:
                    pass
