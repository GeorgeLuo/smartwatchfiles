from typing import List, Tuple, Optional


class Section:
    """
    Represents a section of text or command in the input.

    Attributes:
        raw_text (str): The original raw text of the section.
        opening_labels (List[str]): Labels that mark the beginning of the section.
        closing_labels (List[str]): Labels that mark the end of the section.
        section_type (Optional[str]): The type of the section, either 'text' or 'command'.
        command (Optional[str]): The command associated with the section, if any.
        instruction (Optional[str]): Instructions associated with the command, if any.
        parameters (List[Tuple[str, List[str]]]): Parameters associated with the command, if any.
        text_content (Optional[str]): The text content of the section, if any.
    """
    class SectionType:
        TEXT = "text"
        COMMAND = "command"

    def __init__(self,
                 raw_text: str,
                 opening_labels: Optional[List[str]] = None,
                 closing_labels: Optional[List[str]] = None,
                 section_type: Optional[str] = None,
                 command: Optional[str] = None,
                 instruction: Optional[str] = None,
                 parameters: Optional[List[Tuple[str, List[str]]]] = None,
                 text_content: Optional[str] = None):
        """
        Initializes a Section object.

        Args:
            raw_text (str): The original raw text of the section.
            opening_labels (Optional[List[str]]): Labels that mark the beginning of the section.
            closing_labels (Optional[List[str]]): Labels that mark the end of the section.
            section_type (Optional[str]): The type of the section, either 'text' or 'command'.
            command (Optional[str]): The command associated with the section, if any.
            instruction (Optional[str]): Instructions associated with the command, if any.
            parameters (Optional[List[Tuple[str, List[str]]]]): Parameters associated with the command, if any.
            text_content (Optional[str]): The text content of the section, if any.
        """
        self.raw_text = raw_text
        self.opening_labels: List[str] = opening_labels or []
        self.closing_labels: List[str] = closing_labels or []
        self.section_type: Optional[str] = section_type
        self.command: Optional[str] = command
        self.instruction: Optional[str] = instruction
        self.parameters: List[Tuple[str, List[str]]] = parameters or []
        self.text_content: Optional[str] = text_content

    def __repr__(self):
        return (f"Section(opening_labels={self.opening_labels}, closing_labels={self.closing_labels}, "
                f"section_type={self.section_type}, command={self.command}, instruction={self.instruction}, "
                f"parameters={self.parameters}, text_content={self.text_content})")

    def __eq__(self, other):
        if not isinstance(other, Section):
            return False
        return (self.opening_labels == other.opening_labels and
                self.closing_labels == other.closing_labels and
                self.section_type == other.section_type and
                self.command == other.command and
                self.instruction == other.instruction and
                self.parameters == other.parameters and
                self.text_content == other.text_content)


def parse_section(input_text: str) -> Section:
    """
    Parses the input text and returns a Section object.

    Args:
        input_text (str): The input text to parse.

    Returns:
        Section: The parsed Section object.
    """
    lines = input_text.split('\n')
    opening_labels, closing_labels, section_type, command, instruction, parameters, text_content = parse_lines(
        lines)

    if section_type == Section.SectionType.TEXT:
        return Section(
            raw_text=input_text,
            opening_labels=opening_labels,
            closing_labels=closing_labels,
            section_type=section_type,
            text_content='\n'.join(text_content)
        )
    else:
        return Section(
            raw_text=input_text,
            opening_labels=opening_labels,
            closing_labels=closing_labels,
            section_type=section_type,
            command=command,
            instruction='\n'.join(instruction) if instruction else None,
            parameters=parameters
        )


def parse_lines(lines: List[str]) -> Tuple[List[str], List[str], Optional[str], Optional[str], List[str], List[Tuple[str, List[str]]], List[str]]:
    """
    Parses lines of text and extracts section details.

    Args:
        lines (List[str]): The lines of text to parse.

    Returns:
        Tuple: A tuple containing opening labels, closing labels, section type, command, instruction, parameters, and text content.
    """
    opening_labels = []
    closing_labels = []
    section_type = None
    command = None
    instruction = []
    parameters = []
    text_content = []

    state = 'start'

    for line in lines:
        stripped_line = line.strip()

        if state == 'start':
            state, section_type, command, instruction, opening_labels, text_content = handle_start_state(
                stripped_line, section_type, command, instruction, opening_labels, text_content)

        elif state == 'command':
            state, parameters, instruction = handle_command_state(
                stripped_line, parameters, instruction)

        elif state == 'parameters':
            state, parameters, closing_labels = handle_parameters_state(
                stripped_line, parameters, closing_labels)

        elif state == 'text':
            state, closing_labels, text_content = handle_text_state(
                stripped_line, closing_labels, text_content)

    return opening_labels, closing_labels, section_type, command, instruction, parameters, text_content


def handle_start_state(stripped_line: str, section_type: Optional[str], command: Optional[str], instruction: List[str], opening_labels: List[str], text_content: List[str]) -> Tuple[str, Optional[str], Optional[str], List[str], List[str], List[str]]:
    """
    Handles the 'start' state of parsing.

    Args:
        stripped_line (str): The current line being parsed.
        section_type (Optional[str]): The type of the section.
        command (Optional[str]): The command associated with the section.
        instruction (List[str]): Instructions associated with the command.
        opening_labels (List[str]): Labels that mark the beginning of the section.
        text_content (List[str]): The text content of the section.

    Returns:
        Tuple: A tuple containing the next state, section type, command, instruction, opening labels, and text content.
    """
    if stripped_line.startswith('/'):
        # Collect opening labels
        opening_labels.append(stripped_line[1:])
        return 'start', section_type, command, instruction, opening_labels, text_content
    elif stripped_line.startswith('?'):
        # Identify command section and parse command
        section_type = Section.SectionType.COMMAND
        parts = stripped_line.split(maxsplit=1)
        command = parts[0][1:]
        if len(parts) > 1:
            instruction.append(parts[1])
        return 'command', section_type, command, instruction, opening_labels, text_content
    else:
        # Identify text section and collect text content
        section_type = Section.SectionType.TEXT
        text_content.append(stripped_line)
        return 'text', section_type, command, instruction, opening_labels, text_content


def handle_command_state(stripped_line: str, parameters: List[Tuple[str, List[str]]], instruction: List[str]) -> Tuple[str, List[Tuple[str, List[str]]], List[str]]:
    """
    Handles the 'command' state of parsing.

    Args:
        stripped_line (str): The current line being parsed.
        parameters (List[Tuple[str, List[str]]]): Parameters associated with the command.
        instruction (List[str]): Instructions associated with the command.

    Returns:
        Tuple: A tuple containing the next state, parameters, and instruction.
    """
    if '=' in stripped_line:
        # Parse parameters in command section
        key, value = stripped_line.split('=', 1)
        parameters = add_parameter(parameters, key, value)
        return 'parameters', parameters, instruction
    else:
        # Collect additional instruction lines
        instruction.append(stripped_line)
        return 'command', parameters, instruction


def handle_parameters_state(stripped_line: str, parameters: List[Tuple[str, List[str]]], closing_labels: List[str]) -> Tuple[str, List[Tuple[str, List[str]]], List[str]]:
    """
    Handles the 'parameters' state of parsing.

    Args:
        stripped_line (str): The current line being parsed.
        parameters (List[Tuple[str, List[str]]]): Parameters associated with the command.
        opening_labels (List[str]): Labels that mark the beginning of the section.

    Returns:
        Tuple: A tuple containing the next state, parameters, and opening labels.
    """
    if stripped_line.startswith('\\'):
        # Collect closing labels
        closing_labels.append(stripped_line[1:])
        return 'parameters', parameters, closing_labels
    elif '=' in stripped_line:
        # Parse additional parameters
        key, value = stripped_line.split('=', 1)
        parameters = add_parameter(parameters, key, value)
        return 'parameters', parameters, closing_labels
    else:
        raise ValueError(
            f"Unexpected line in parameters state: {stripped_line}")


def handle_text_state(stripped_line: str, closing_labels: List[str], text_content: List[str]) -> Tuple[str, List[str], List[str]]:
    """
    Handles the 'text' state of parsing.

    Args:
        stripped_line (str): The current line being parsed.
        closing_labels (List[str]): Labels that mark the end of the section.
        text_content (List[str]): The text content of the section.

    Returns:
        Tuple: A tuple containing the next state, closing labels, and text content.
    """
    if stripped_line.startswith('\\'):
        # Collect closing labels
        closing_labels.append(stripped_line[1:])
        return 'text', closing_labels, text_content
    else:
        # Collect additional text content
        text_content.append(stripped_line)
        return 'text', closing_labels, text_content


def add_parameter(parameters: List[Tuple[str, List[str]]], key: str, value: str) -> List[Tuple[str, List[str]]]:
    """
    Adds a parameter to the list of parameters.

    Args:
        parameters (List[Tuple[str, List[str]]]): The current list of parameters.
        key (str): The parameter key.
        value (str): The parameter value.

    Returns:
        List[Tuple[str, List[str]]]: The updated list of parameters.
    """
    for param in parameters:
        if param[0] == key:
            param[1].append(value)
            break
    else:
        parameters.append((key, [value]))
    return parameters
