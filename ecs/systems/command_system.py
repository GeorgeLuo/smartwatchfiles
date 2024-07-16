import os
import re
import shlex
import subprocess
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
import requests
from command_handlers.insert import handle_insert_command
from command_handlers.llm import Model, build_query, call_llm, generate_readable
from ecs.components.command_component import CommandComponent
from ecs.components.instruction_component import InstructionComponent
from ecs.components.parameters_component import ParametersComponent
from ecs.components.rendered_text_component import set_rendered_text_component
from ecs.managers.component_manager import ComponentManager, Entity
from ecs.managers.entity_manager import EntityManager
from ecs.utils.config_util import get_latest_or_config, get_latest_parameter
import hashlib
import json

from ecs.utils.files_util import append_to_file, write_to_file
from ecs.utils.web_util import download_and_parse


def get_model(component_manager: ComponentManager, parameters: List[Tuple[str, List[str]]]) -> Optional[Model]:
    """
    Retrieve the latest parameter value for the given config key and "llm-api-key". 
    If not found, get the config value from the component manager.

    Args:
        component_manager (ComponentManager): The component manager instance.
        parameters (List[Tuple[str, List[str]]]): List of parameters.

    Returns:
        Optional[Model]: The model configuration, or None if not found.
    """

    # Retrieve the llm name
    llm_name = get_latest_or_config(parameters, "llm", component_manager)
    # Retrieve the llm-api-key
    llm_api_key = get_latest_or_config(
        parameters, "llm-api-key", component_manager)

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
    rendered_text = handle_insert_command(
        parameters_component.render_parameters)
    set_rendered_text_component(component_manager, entity, rendered_text)


def run_continuously(parameters) -> bool:
    val = next(
        (param[1][0] for param in parameters if param[0] == 'run_continuous'), None)
    return val == "true"


def generate_run_key(instruction, parameters, entity: Entity) -> str:
    # Create a unique string from the instruction, parameters, and entity
    unique_string = json.dumps({
        "instruction": instruction,
        "parameters": parameters,
        "entity": entity
    }, sort_keys=True)

    # Generate a hash key from the unique string
    key = hashlib.md5(unique_string.encode()).hexdigest()
    return key


def handle_run(entity: Entity, component_manager: ComponentManager, run_cache: dict):
    """
    Handle the 'run' command by executing the instruction as a system command and updating the rendered text component with the result.

    Args:
        entity: The entity to which the command belongs.
        component_manager (ComponentManager): The component manager instance.
        run_cache (dict): Cache dictionary to store run results.
    """
    instruction_comp = component_manager.get_component(
        entity, InstructionComponent)
    instruction = instruction_comp.render_instruction

    parameters = component_manager.get_component(
        entity, ParametersComponent).parameters

    query_key = generate_run_key(
        instruction_comp.render_instruction, parameters, entity)
    cache_value = run_cache.get(query_key)

    if cache_value and not run_continuously(parameters):
        set_rendered_text_component(component_manager, entity, cache_value)
        return

    try:
        cmd_parts = shlex.split(instruction)
        if cmd_parts[0].lower() == "python":
            python_exec = get_latest_or_config(
                parameters, "python-exec", component_manager)
            cmd_parts[0] = python_exec

        process = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            result = f"{stdout}"
            run_cache[query_key] = result
        else:
            result = f"Command failed with return code {process.returncode}.\nError:\n{stderr}"
        set_rendered_text_component(component_manager, entity, result)
    except Exception as e:
        error_message = f"An error occurred while executing the command: {str(e)}"
        set_rendered_text_component(component_manager, entity, error_message)


def handle_gen(entity, component_manager: ComponentManager, gen_cache: dict, web_cache: dict):
    """
    Handle the 'gen' command by generating text using a language model and updating the rendered text component.

    Args:
        entity: The entity to which the command belongs.
        component_manager (ComponentManager): The component manager instance.
        gen_cache (dict): Cache for language model responses.
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
    cache_value = gen_cache.get(query_key)

    if cache_value and not cache_value.rate_limited:
        rendered_text = cache_value.response
    else:
        if instruction == 'web':
            link = get_latest_parameter(parameters, 'link')

            if link in web_cache:
                site_text = web_cache[link]
            else:
                site_text = download_and_parse(link)
                web_cache[link] = site_text

            parse = get_latest_parameter(parameters, 'parse')
            if parse == 'readable':
                error, rendered_text = generate_readable(
                    site_text, parameters, model)
            else:
                error, rendered_text = (False, site_text)
        else:
            error, rendered_text = call_llm(
                instruction, parameters, model)

        gen_cache[query_key] = LLMCacheValue(rendered_text, error)
        write_params = next(
            (param[1] for param in parameters if param[0] == 'write'), None)
        if write_params:
            write_to_file(write_params[0], rendered_text)

        write_append_params = next(
            (param[1] for param in parameters if param[0] == 'write_append'), None)
        if write_append_params:
            append_to_file(write_append_params[0], rendered_text)

    set_rendered_text_component(component_manager, entity, rendered_text)


def handle_web(entity, component_manager: ComponentManager, web_cache: dict):
    # get the url from the instruction component
    instruction = component_manager.get_component(
        entity, InstructionComponent).render_instruction

    parameters_comp = component_manager.get_component(
        entity, ParametersComponent)
    parameters = parameters_comp.render_parameters

    site_text = download_and_parse(instruction, parameters)
    set_rendered_text_component(component_manager, entity, site_text)


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
        gen_cache (dict): Cache for language model responses.
    """

    def __init__(self) -> None:
        self.gen_cache = {}
        self.run_cache = {}
        self.web_cache = {}

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
                    parameters = component_manager.get_component(
                        entity, ParametersComponent)
                    handle_insert(entity, component_manager, parameters)
                case "gen":
                    handle_gen(entity, component_manager,
                               self.gen_cache, self.web_cache)
                case "run":
                    handle_run(entity, component_manager, self.run_cache)
                case "web":
                    handle_web(entity, component_manager, self.web_cache)
                case _:
                    pass
