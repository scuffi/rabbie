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
from types import ModuleType
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserverVFS

from loguru import logger as log

import importlib
import imp
from pydoc import importfile

class Supervisor:
    def __init__(
        self, path: str, regex: str = r"(\.py)$", recursive: bool = True, start_function: Callable = None, stop_function: Callable = None
    ) -> None:
        
        # Function to run when the Supervisor has started
        self._start_function = start_function
        
        # Function to call when the supervisor is stopping/restarting
        self._stop_function = stop_function
        
        self._event_handler = FileChangeEvent(regex, self)
        self._observer = PollingObserverVFS(
            stat=os.stat, listdir=os.scandir, polling_interval=0.1
        )

        self._path = path
        self._observer.schedule(self._event_handler, self._path, recursive=recursive)

        # self.process: Optional[mp.Process] = None

    def stop(self):
        if True:
            log.info("Stopping runner")
            log.info("Waiting for active tasks to conclude...")
            
            # Execute any specified stop callback.
            self._stop_function()
            
            # Kill the process
            # self.process.kill()
            # self.process = None
            log.info("Runner stopped")
            
    def start(self):
        # self.process = mp.Process(target=self._start_function)
        log.info("Starting runner")
        # self.process.start()
        self._start_function()

    def restart(self):
        log.info("Restarting service...")
        self.stop()
        self.start()
    
    def listen(self):
        log.success(f"Listening for changes in '{self._path}'")
        self._observer.start()
        self.start()

class FileChangeEvent(FileSystemEventHandler):
    def __init__(self, regex: str, supervisor: Supervisor) -> None:
        super().__init__()

        self.pattern = regex
        self.supervisor = supervisor

    def on_any_event(self, event):
        # Under no circumstances do we want to reload a directory
        if event.is_directory:
            return

        path: str = event.src_path

        # This should counteract the directory check anyways, but check that our file path matches our regex
        if re.search(pattern=self.pattern, string=path):
            module = importfile(path)
            # TODO: Here will add listeners again, we don't want to do this.
            log.warning(f"Detected changes in {module.__name__}")
            
            # Stop the supervisor listeners
            self.supervisor.stop()
            
            # Reload the module so it loads up when nothing is running.
            self.reloadModuleWithChildren(module)
            
            # Start the supervisor listeners again
            self.supervisor.start()
            
    def reloadModuleWithChildren(self, mod):
        mod = importlib.reload(mod)
        for k, v in mod.__dict__.items():
            if isinstance(v, ModuleType):
                setattr(mod, k, importlib.import_module(v.__name__))