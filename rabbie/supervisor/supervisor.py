# Brainstorm

# Register a FileWatcher for all files in given directory
# Create an event callback that filters out Regex files (ones that don't end in .py)
# Take the main thread function as an argument in init
# After Supervisor has setup all above, run the main thread function in a process
# The main thread can be halted.
# The event handler should reload the given file in the event
# The event handler should then call the Supervisor and say reload
# The supervisor should then join the current process
# When the current process is finished, plainly start the process again like it did before
import os
import re
import multiprocessing as mp
from typing import Optional, Callable
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserverVFS

import importlib
from pydoc import importfile


class Supervisor:
    def __init__(
        self, path: str, regex: str = r"(\.py)$", recursive: bool = True
    ) -> None:
        self._event_handler = FileChangeEvent(regex)
        self._observer = PollingObserverVFS(
            stat=os.stat, listdir=os.scandir, polling_interval=0.1
        )

        self._observer.schedule(self._event_handler, path, recursive=recursive)

        self.process: Optional[mp.Process] = None

    def stop(self):
        if self.process:
            print("Stopping runner")
            print("Waiting for active tasks to conclude...")
            self.process.join()
            self.process = None
            print("Runner stopped")

    def start(self, target: Callable):
        self.process = mp.Process(target=target)
        print("Starting runner")
        self.process.start()

    def restart(self):
        print("Restarting service...")
        self.stop()
        self.start()


class FileChangeEvent(FileSystemEventHandler):
    def __init__(self, regex: str) -> None:
        super().__init__()

        self.pattern = regex

    def on_any_event(self, event):

        # Under no circumstances do we want to reload a directory
        if event.is_directory:
            return

        path: str = event.src_path

        # This should counteract the directory check anyways, but check that our file path matches our regex
        if re.match(pattern=self.pattern, string=path):
            module = importfile(path)

            print(f"Detected changes in {module.__name__}")
            importlib.reload(module)
