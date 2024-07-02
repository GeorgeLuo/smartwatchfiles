import logging
from pathlib import Path
import threading
import os
import sys
from typing import Tuple
from ecs.ecs_app import ECSApp

from ecs.systems.generator_parsing_system import GeneratorParsingSystem
from ecs.systems.label_embedding_system import LabelEmbeddingSystem
from ecs.systems.command_system import CommandSystem
from ecs.systems.render_system import RenderSystem

from ecs.event_bus import EventBus
from filewatcher import FileWatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_file_path(file_base_name: str, extension: str, base_path: Path) -> Path:
    file_path = base_path / f"{file_base_name}{extension}"
    if not file_path.exists():
        file_path.touch()
        logging.info(f"Created file: {file_path}")
    return file_path


def setup_files(file_base_name: str, path: str) -> Tuple[Path, Path]:
    full_base_path = Path(os.path.abspath(path))

    # Generate paths for generator and generated files
    generator_file_path = get_file_path(file_base_name, '.gen', full_base_path)
    generated_file_path = get_file_path(file_base_name, '.txt', full_base_path)

    return (generated_file_path, generator_file_path)


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python main.py <base-file-name> [path]")
        sys.exit(1)

    file_base_name = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) == 3 else "."

    generated_file, generator_file = setup_files(file_base_name, path)

    ecs_app_config = {
        "generator_file": generator_file,
        "generated_file": generated_file
    }

    event_bus = EventBus()

    watcher = FileWatcher(generator_file, event_bus)
    watcher_thread = threading.Thread(target=watcher.start)
    watcher_thread.daemon = True
    watcher_thread.start()

    app = ECSApp()

    app.add_system(GeneratorParsingSystem(event_bus))
    app.add_system(LabelEmbeddingSystem())
    app.add_system(CommandSystem())
    app.add_system(RenderSystem(generated_file))

    event_bus.push_event(
        "file_modified", {"file_name": generator_file})

    app.run()
