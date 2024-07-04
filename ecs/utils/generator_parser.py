import re


def split_into_sections(content: str) -> list[dict]:
    """
    Splits the input content into sections based on double newlines.

    Args:
        content (str): The input text content to be split into sections.

    Returns:
        list[dict]: A list of dictionaries, each containing the raw text of a section.

    Business Logic:
        - The content is split into sections using double newlines as delimiters.
        - Each section is stored in a dictionary with the key 'raw_text'.
    """
    # Use a regular expression to split the content into sections based on double newlines
    raw_sections = re.split(r'\n\s*\n', content.strip())
    # Create a list of section dictionaries
    sections = [{'raw_text': section.strip()} for section in raw_sections]
    return sections


def parse_section(section: dict) -> dict:
    """
    Parses a single section to determine its type and extract relevant information.

    Args:
        section (dict): A dictionary containing the raw text of the section.

    Returns:
        dict: A dictionary containing the parsed section information.

    Business Logic:
        - Determines if the section is a command section or a text section.
        - If it's a command section, it parses the command and its parameters.
        - If it's a text section, it simply returns the raw text.
    """
    raw_text = section['raw_text']

    if is_command_section(raw_text):
        return parse_command_section(raw_text)
    else:
        return {
            'section_type': 'text',
            'raw_text': raw_text
        }


def is_command_section(raw_text: str) -> bool:
    """
    Checks if a section is a command section.

    Args:
        raw_text (str): The raw text of the section.

    Returns:
        bool: True if the section is a command section, False otherwise.

    Business Logic:
        - A section is considered a command section if it starts with a '?' and ends with a '.' on a newline.
    """
    # Check if the section starts with a '?' and ends with a '.' on a newline
    return raw_text.startswith('?') and raw_text.strip().endswith('\n.')


def parse_command_section(raw_text: str) -> dict:
    """
    Parses a command section to extract the command, instruction, and parameters.

    Args:
        raw_text (str): The raw text of the command section.

    Returns:
        dict: A dictionary containing the parsed command section information.

    Business Logic:
        - Extracts the command and instruction from the first line.
        - Extracts parameters from the subsequent lines.
    """
    lines = raw_text.splitlines()
    command_line = lines[0][1:].strip()  # Remove the initial '?'
    command, instruction = split_command_line(command_line)

    parameters = extract_parameters(lines[1:])

    return {
        'section_type': 'command',
        'command': command,
        'instruction': instruction,
        'parameters': parameters,
        'raw_text': raw_text
    }


def split_command_line(command_line: str) -> tuple[str, str]:
    """
    Splits the command line into command and instruction.

    Args:
        command_line (str): The command line text.

    Returns:
        tuple[str, str]: A tuple containing the command and instruction.

    Business Logic:
        - Splits the command line into two parts: the command and the instruction.
    """
    parts = command_line.split(' ', 1)
    command = parts[0]
    instruction = parts[1] if len(parts) > 1 else ""
    return command, instruction


def extract_parameters(lines: list[str]) -> dict:
    """
    Extracts parameters from the lines of a command section.

    Args:
        lines (list[str]): The lines of text following the command line.

    Returns:
        dict: A dictionary containing the parameters as key-value pairs.

    Business Logic:
        - Each line containing an '=' is considered a parameter line.
        - Splits each parameter line into key and value.
    """
    parameters = {}
    for line in lines:
        if '=' in line:
            key, value = line.split('=', 1)
            parameters[key.strip()] = value.strip()
    return parameters


def parse_sections(sections: list[dict]) -> list[dict]:
    """
    Parses a list of sections to extract detailed information from each section.

    Args:
        sections (list[dict]): A list of section dictionaries to be parsed.

    Returns:
        list[dict]: A list of dictionaries containing parsed section information.

    Business Logic:
        - Iterates over each section and parses it using the parse_section function.
    """
    # Iterate over each section and parse it
    return [parse_section(section) for section in sections]
