from typing import List, Tuple


def get_latest_parameter(parameters: List[Tuple[str, List[str]]], key: str) -> str:
    for parameter in parameters:
        if parameter[0] == key:
            return parameter[1][-1]


class CommandComponent:
    def __init__(self, command: str, parameters: List[Tuple[str, List[str]]]):
        self.command = command
        self.instruction = ''
        self.parameters = parameters
