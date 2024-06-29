import re
from typing import List, Tuple, Optional


class Section:
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
    lines = input_text.split('\n')
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
            if stripped_line.startswith('/'):
                # Collect opening labels
                opening_labels.append(stripped_line[1:])
            elif stripped_line.startswith('?'):
                # Identify command section and parse command
                section_type = Section.SectionType.COMMAND
                parts = stripped_line.split(maxsplit=1)
                command = parts[0][1:]
                if len(parts) > 1:
                    instruction.append(parts[1])
                state = 'command'
            else:
                # Identify text section and collect text content
                section_type = Section.SectionType.TEXT
                text_content.append(stripped_line)
                state = 'text'

        elif state == 'command':
            if '=' in stripped_line:
                # Parse parameters in command section
                key, value = stripped_line.split('=', 1)
                # Check if key already exists in parameters
                for param in parameters:
                    if param[0] == key:
                        param[1].append(value)
                        break
                else:
                    parameters.append((key, [value]))
                state = 'parameters'
            else:
                # Collect additional instruction lines
                instruction.append(stripped_line)

        elif state == 'parameters':
            if stripped_line.startswith('\\'):
                # Collect closing labels
                opening_labels.append(stripped_line[1:])
            elif '=' in stripped_line:
                # Parse additional parameters
                key, value = stripped_line.split('=', 1)
                # Check if key already exists in parameters
                for param in parameters:
                    if param[0] == key:
                        param[1].append(value)
                        break
                else:
                    parameters.append((key, [value]))
            else:
                raise ValueError(
                    f"Unexpected line in parameters state: {stripped_line}")

        elif state == 'text':
            if stripped_line.startswith('\\'):
                # Collect closing labels
                closing_labels.append(stripped_line)
            else:
                # Collect additional text content
                text_content.append(stripped_line)

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
