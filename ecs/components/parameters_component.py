from typing import List, Tuple


class ParametersComponent():
    def __init__(self, parameters: List[Tuple[str, List[str]]]) -> None:
        self.parameters = parameters
        self.render_parameters = parameters
