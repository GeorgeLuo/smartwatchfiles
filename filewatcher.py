import os
import logging
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import json

from ecs.event_bus import EventBus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_generator_file_path(file_base_name):
    instruction_file_path = Path(file_base_name)
    if not instruction_file_path.exists():
        gen_file_path = instruction_file_path.with_suffix('.gen')
        if not gen_file_path.exists():
            gen_file_path.touch()
            logging.info(f"Created instruction file: {gen_file_path}")
        return gen_file_path
    return instruction_file_path


def ensure_files_exist(generated_file_path):
    if not generated_file_path.exists():
        generated_file_path.touch()
        logging.info(f"Created generated file: {generated_file_path}")


def compute_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as file:
        buf = file.read()
        hasher.update(buf)
    return hasher.hexdigest()


class FileWatcher(FileSystemEventHandler):
    """    
    generator_file_path : Path
        The path to the generator file based on the provided base name.

    generated_file_path : Path
        The path to the generated file with a .txt suffix.

    state_file_path : Path
        The path to the state file with a .state.json suffix.
    """

    def __init__(self, file_base_name, event_bus: EventBus, full_generator_path=None):

        # Setup the generator
        self.generator_file_path = get_generator_file_path(file_base_name)
        self.generator_full_path = full_generator_path + "/" + file_base_name + ".gen"

        # Convert the raw .gen file into object and compute hash
        with open(self.generator_file_path, 'r') as generator_file:
            content = generator_file.read()
            version_hash = compute_hash(self.generator_file_path)

        # Setup paths for generated and state files
        self.generated_file_path = self.generator_file_path.with_suffix('.txt')
        ensure_files_exist(self.generated_file_path)
        self.state_file_path = self.generator_file_path.with_suffix(
            '.state.json')
        self._ensure_state_file_exist()

        self.event_bus = event_bus

    def _ensure_state_file_exist(self):
        """
        Ensure that the state file exists. If it does not, create it.
        """
        state_file_path = Path(self.state_file_path)
        if not state_file_path.exists():
            # Create the file
            state_file_path.touch()
            logging.info(f"Created state file: {state_file_path}")

            # Populate the file with the default JSON blob
            default_content = {
                "version_hash": None,
                "sections": []
            }
            with state_file_path.open('w', encoding='utf-8') as file:
                json.dump(default_content, file, indent=4)
            logging.info(
                f"Populated state file with default content: {state_file_path}")

    def on_modified(self, event):
        if event.src_path == self.generator_full_path:
            self.event_bus.push_event(
                "file_modified", {"file_name": event.src_path})

    def start(self):
        observer = Observer()
        observer.schedule(
            self, self.generator_file_path.parent, recursive=False)
        observer.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
