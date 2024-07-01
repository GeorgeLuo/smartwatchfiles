from typing import Dict


class ConfigComponent():
    def __init__(self, config_map: Dict[str, str]) -> None:
        self.config_map = config_map