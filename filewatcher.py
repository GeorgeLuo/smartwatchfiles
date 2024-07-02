import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

from ecs.event_bus import EventBus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


class FileWatcher(FileSystemEventHandler):
    """    
    generator_file_path : Path
        The path to the generator file based on the provided base name.

    generated_file_path : Path
        The path to the generated file with a .txt suffix.
    """

    def __init__(self, generator_full_path: Path, event_bus: EventBus, full_generator_path=None):

        self.generator_full_path = generator_full_path

        self.event_bus = event_bus

    def on_modified(self, event):
        src_path = event.src_path
        absolute = str(self.generator_full_path)
        if event.src_path == str(self.generator_full_path):
            self.event_bus.push_event(
                "file_modified", {"file_name": event.src_path})

    def start(self):
        observer = Observer()
        observer.schedule(
            self, self.generator_full_path.parent, recursive=False)
        observer.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
