###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################

import threading
from queue import PriorityQueue
from . import autollm  # Assurez-vous d'importer correctement le module
from . import digest
import time  # Importer le module time

# Create the priority queue
task_queue = PriorityQueue()

def add_task(priority, function, *args, **kwargs):
    """Add a task to the queue with specified priority, function, and arguments."""
    print(" === )) task added")
    task_queue.put((priority, (function, args, kwargs)))

def thread_task(function, args, kwargs):
    """Function wrapper to execute tasks from the queue."""
    print(f"[DEBUG] Executing task: {function.__name__} with args: {args} and kwargs: {kwargs}")
    function(*args, **kwargs)
    print(f"[DEBUG] Task {function.__name__} completed")

def thread_manager():
    """Manage and execute threads based on the tasks in the queue."""
    print("[DEBUG] Starting thread manager")
    while True:  # Keep the manager running
        if not task_queue.empty():
            priority, (function, args, kwargs) = task_queue.get()
            print(f"[DEBUG] Retrieved task {function.__name__} with priority {priority}")
            thread = threading.Thread(target=thread_task, args=(function, args, kwargs))
            thread.start()
            thread.join()  # Wait for the task to complete
            task_queue.task_done()
            print(f"[DEBUG] Task {function.__name__} done")
        time.sleep(0.1)  # Prevent busy-waiting

def start_autosession_task(message):
    print(f"[DEBUG] Starting auto session with message: {message}")
    autollm.threaded_autosession(message)

def start_rag_task(message,tag):
    print(f"[DEBUG] Starting rag with message: {tag} / {message}")
    autollm.threaded_autosession(message,tag)

def start_digest_url_task(url,scrabbing,tag):
    print(f"[DEBUG] Starting digest url task  {url} {scrabbing}")
    digest.scrab_webpages(url,scrabbing,tag)

def start_digest_doc_task(file_path,tag):
    print(f"[DEBUG] Starting digest doc task  {file_path}")
    digest.process_text_file(file_path,tag)
