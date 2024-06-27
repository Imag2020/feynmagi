import threading
from queue import PriorityQueue, Queue
from . import autollm  # Assurez-vous d'importer correctement le module
from . import digest
import time  # Importer le module time

# Create the priority queue and a dictionary for queues by priority
task_queues = {}
priority_locks = {}

def add_task(priority, function, *args, **kwargs):
    """Add a task to the queue with specified priority, function, and arguments."""
    if priority not in task_queues:
        task_queues[priority] = Queue()
        priority_locks[priority] = threading.Lock()
    print(" === )) task added")
    task_queues[priority].put((function, args, kwargs))

def thread_task(function, args, kwargs):
    """Function wrapper to execute tasks from the queue."""
    thread_id = threading.get_ident()
    print(f"_________ [DEBUG] Executing task: {function.__name__} with args: {args} and kwargs: {kwargs} on thread {thread_id}")
    function(*args, **kwargs)
    print(f" _________ [DEBUG] Task {function.__name__} completed on thread {thread_id}")

def thread_manager():
    """Manage and execute threads based on the tasks in the queue."""
    print("[DEBUG] Starting thread manager")
    while True:  # Keep the manager running
        for priority in sorted(task_queues.keys()):
            if not task_queues[priority].empty():
                function, args, kwargs = task_queues[priority].get()
                print(f"======== [DEBUG] Retrieved task {function.__name__} with priority {priority}")
                with priority_locks[priority]:  # Ensure only one thread at this priority level
                    thread = threading.Thread(target=thread_task, args=(function, args, kwargs))
                    thread.start()
                    thread.join()  # Wait for the task to complete
                task_queues[priority].task_done()
                print(f" ======== [DEBUG] Task {function.__name__} done")
        time.sleep(0.1)  # Prevent busy-waiting

def start_autosession_task(message):
    print(f"[DEBUG] Starting auto session with message: {message}")
    autollm.threaded_autosession(message)

def start_rag_task(message, tag):
    print(f"[DEBUG] Starting rag with message: {tag} / {message}")
    autollm.threaded_autosession(message, tag)

def start_digest_url_task(url, scrabbing, tag):
    print(f"[DEBUG] Starting digest url task {url} {scrabbing}")
    digest.scrab_webpages(url, scrabbing, tag)

def start_digest_doc_task(file_path, tag):
    print(f"[DEBUG] Starting digest doc task {file_path}")
    digest.process_text_file(file_path, tag)
