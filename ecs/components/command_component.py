from typing import List, Tuple


class CommandComponent:
    def __init__(self, command: str, parameters: List[Tuple[str, List[str]]]):
        self.command = command
        self.instruction = ''
        self.parameters = parameters
