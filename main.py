import threading
import os
import sys
from ecs.ecs_app import ECSApp

from ecs.systems.generator_parsing_system import GeneratorParsingSystem
from ecs.systems.label_embedding_system import LabelEmbeddingSystem
from ecs.systems.command_system import CommandSystem
from ecs.systems.render_system import RenderSystem

from ecs.event_bus import EventBus
from filewatcher import FileWatcher

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script.py <base-file-name> [path]")
        sys.exit(1)

    file_base_name = sys.argv[1]
    event_bus = EventBus()

    path = sys.argv[2] if len(sys.argv) == 3 else "."

    watcher = FileWatcher(file_base_name, event_bus,
                          full_generator_path=os.path.join(os.path.abspath(path)))
    watcher_thread = threading.Thread(target=watcher.start)
    watcher_thread.daemon = True
    watcher_thread.start()

    # Example usage
    app = ECSApp()

    app.add_system(GeneratorParsingSystem(event_bus))
    app.add_system(LabelEmbeddingSystem())
    app.add_system(CommandSystem())
    app.add_system(RenderSystem())

    event_bus.push_event(
        "file_modified", {"file_name": os.path.join(os.path.abspath(path) + "/" + file_base_name + ".gen")})

    app.run()
