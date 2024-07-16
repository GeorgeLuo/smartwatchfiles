import time
from typing import List, NamedTuple, Tuple
from openai import OpenAI
import logging
import hashlib

disable = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

last_call_time = 0
rate_limit_seconds = 10

RENDER_TEXT_RATE_LIMITED = '<LLM RATE LIMIT>'


class Model(NamedTuple):
    name: str
    api_key: str


def build_query(instruction: str, parameters: List[Tuple[str, List[str]]], model: str) -> Tuple[str, str]:
    """
    Constructs a query string and a unique key based on the instruction, parameters, and model name.

    Args:
        instruction (str): The instruction to be sent to the LLM.
        parameters (List[Tuple[str, List[str]]]): A list of parameters where each parameter is a tuple
                                                  containing the parameter name and a list of values.
        model (str): The name of the model to be used.

    Returns:
        Tuple[str, str]: A tuple containing the constructed query string and a unique key.
    """
    query = instruction

    # Look for "file" key in parameters and append file contents to query
    query = append_file_contents_to_query(query, parameters)

    # Create key as hash of instructions and parameters
    key = hashlib.md5(
        (instruction + model + str(parameters)).encode()).hexdigest()

    return query, key


def append_file_contents_to_query(query: str, parameters: List[Tuple[str, List[str]]]) -> str:
    """
    Appends the contents of files specified in the parameters to the query string.

    Args:
        query (str): The initial query string.
        parameters (List[Tuple[str, List[str]]]): A list of parameters where each parameter is a tuple
                                                  containing the parameter name and a list of values.

    Returns:
        str: The query string with appended file contents.
    """
    for param_name, param_values in parameters:
        if param_name == "file":
            for file_path in param_values:
                try:
                    with open(file_path, 'r') as file:
                        file_content = file.read()
                        query += f"\n\nContent of file {file_path}:\n{file_content}"
                except IOError as e:
                    logging.error(f"Error reading file {file_path}: {e}")
    return query


def extract_code_blocks(rendered_text: str) -> str:
    """
    Extracts code blocks from the rendered text.

    Args:
        rendered_text (str): The text rendered by the LLM.

    Returns:
        str: The extracted code blocks or a message indicating no code block was found.
    """
    # Split the text by tick blocks
    blocks = rendered_text.split('```')

    # Extract content from tick blocks (odd-indexed elements)
    code_blocks = ['\n'.join(block.split('\n')[1:]).strip()
                   for block in blocks[1::2]]

    # Concatenate all code blocks
    extracted_code = '\n'.join(code_blocks).strip()

    if not extracted_code:
        extracted_code = "No code block found in the response."

    return extracted_code


def generate_readable(text: str, parameters: List[Tuple[str, List[str]]], model: Model) -> Tuple[bool, str]:
    """
    Generates a readable version of the provided HTML text by calling the LLM with specific instructions.

    Args:
        text (str): The HTML text to be processed.
        parameters (List[Tuple[str, List[str]]]): A list of parameters where each parameter is a tuple
                                                  containing the parameter name and a list of values.
        model (Model): The model configuration containing the name and API key.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if an error occurred and the rendered readable text.
    """

    instruction = """render the following text extracted from html to be readable,
    retaining details and completeness of the body while removing elements
    that are part of the page navigation. Do not editorialize, just output the readable text."""
    # Appending the text to the instruction
    combined_instruction = f"{instruction}\n\n{text}"

    # Calling the LLM utility function
    error, response_text = call_llm(combined_instruction, parameters, model)

    return error, response_text


def call_llm(instruction: str, parameters: List[Tuple[str, List[str]]], model: Model) -> Tuple[bool, str]:
    """
    Calls the LLM API with the given instruction, parameters, and model configuration.

    Args:
        instruction (str): The instruction to be sent to the LLM.
        parameters (List[Tuple[str, List[str]]]): A list of parameters where each parameter is a tuple
                                                  containing the parameter name and a list of values.
        model (Model): The model configuration containing the name and API key.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if an error occurred and the response text.
    """

    # TODO: important the error signal and the rate limit signal are confused

    global last_call_time
    current_time = time.time()

    # Check for rate limiting
    if is_rate_limited(current_time):
        logging.info("Rate limit in effect. Returning rate limited response.")
        return (True, RENDER_TEXT_RATE_LIMITED)

    # Check if LLM is disabled
    if disable:
        logging.info(instruction)
        return (False, "test response")

    # Build the query and key
    query, key = build_query(instruction, parameters, model.name)

    # Check if code extraction is needed
    extract_code = should_extract_code(parameters)

    # Extract max_tokens if present
    max_tokens = None
    for param, values in parameters:
        if param == "max-tokens" and values:
            max_tokens = int(values[0])
            break

    try:
        # Call the LLM API
        rendered_text = call_llm_api(model, query, max_tokens=max_tokens)

        last_call_time = current_time

        # Extract code blocks if needed
        if extract_code:
            rendered_text = extract_code_blocks(rendered_text)

        return (False, rendered_text)

    except Exception as e:
        logging.error(f"Error calling LLM: {str(e)}")
        return (True, f"Error: {str(e)}")


def is_rate_limited(current_time: float) -> bool:
    """
    Checks if the current time is within the rate limit period.

    Args:
        current_time (float): The current time in seconds.

    Returns:
        bool: True if the current time is within the rate limit period, False otherwise.
    """
    global last_call_time

    return current_time - last_call_time <= rate_limit_seconds


def should_extract_code(parameters: List[Tuple[str, List[str]]]) -> bool:
    """
    Determines if code extraction is needed based on the parameters.

    Args:
        parameters (List[Tuple[str, List[str]]]): A list of parameters where each parameter is a tuple
                                                  containing the parameter name and a list of values.

    Returns:
        bool: True if code extraction is needed, False otherwise.
    """
    return any(param[0] == "extract" and "code" in param[1] for param in parameters)


def call_llm_api(model: Model, query: str, max_tokens: int = None) -> str:
    """
    Calls the LLM API and returns the response.

    Args:
        model (Model): The model configuration containing the name and API key.
        query (str): The query string to be sent to the LLM.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to None.

    Returns:
        str: The response text from the LLM.

    Raises:
        ValueError: If the model name is unsupported.
    """
    if model.name.startswith('gpt'):
        client = OpenAI(api_key=model.api_key)
        request_payload = {
            "model": model.name,
            "messages": [
                {"role": "user", "content": query},
            ],
            "temperature": 0,
        }
        if max_tokens is not None:
            request_payload["max_tokens"] = max_tokens

        response = client.chat.completions.create(**request_payload)
        return response.choices[0].message.content
    else:
        raise ValueError(f"Unsupported model: {model.name}")
