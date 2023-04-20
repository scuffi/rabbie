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
from typing import Callable
from types import ModuleType
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserverVFS

import importlib
from pydoc import importfile

from ..logger import logger as log

import sys

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

    def stop(self):
        log.debug("Stopping runner")
        log.debug("Waiting for active tasks to conclude...")
        
        # Execute any specified stop callback.
        self._stop_function()
        
        log.debug("Runner stopped")
            
    def start(self):
        log.debug("Starting runner")
        self._start_function()

    def listen(self):
        log.info(f"Listening for changes in '{self._path}'")
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

        log.debug(f"Detected change in {path}")
        # This should counteract the directory check anyways, but check that our file path matches our regex
        if re.search(pattern=self.pattern, string=path):
            # module = importfile(path)
            # log.warning(f"Detected changes in {module.__name__}, listeners will reload...")
            
            # Stop the supervisor listeners
            self.supervisor.stop()
            
            log.critical("[bold red]STOPPED")
            
            # Reload the module so it loads up when nothing is running.
            # self.reloadModuleWithChildren(module)
            # Get a list of all imported modules
            log.debug(sys.modules)
            modules = [m for m in sys.modules.values() if m is not None]

            # Reload all modules that were imported from __main__
            for module in modules:
                if hasattr(module, '__name__'):
                    log.debug(f"Reloading {module.__name__}")
                    importlib.reload(module)
                    
            log.debug("Reloaded module")
            
            # TODO: First empty the listeners list (keep a copy for future)
            
            # TODO: First reload the changed module, this module could have updated logic outside of listeners
            
            # TODO: Then reload all of the known listener modules (ensure that no duplicate function from before was added)
            
            # TODO: Then start the code back up again with the new listeners
            
            # Start the supervisor listeners again
            self.supervisor.start()
            
    def reloadModuleWithChildren(self, mod):
        # import inspect
        log.debug(f"Reloading {mod.__name__}")
        mod = importlib.reload(mod)
        # for k, v in mod.__dict__.items():
        #     # v = inspect.getmodule(v)
        #     if isinstance(v, ModuleType):
        #         reloaded_child = importlib.reload(v)
        #         setattr(mod, k, importlib.import_module(v.__name__))