# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import queue
import threading
from functools import wraps

task_queue = queue.Queue()


def call_directly(func):
    """Decorator to directly call a function Without caring about threading."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def run_in_main_thread(func):
    """Decorator to ensure a function runs on the main thread."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            return func(*args, **kwargs)
        else:
            # Create a queue to hold the result
            result_queue = queue.Queue()

            # Define a function to execute and store the result
            def task():
                result = func(*args, **kwargs)
                result_queue.put(result)

            # Put the task function on the task queue
            task_queue.put(task)

            # Wait for the result and return it
            return result_queue.get()

    return wrapper


def delegate_to_main_thread_wrapper(func):
    '''
    Decorator to ensure a function runs on the main thread. Using the
    run_in_main_thread_wrapper function passed to the instancied class.
    '''

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.run_in_main_thread_wrapper:
            return self.run_in_main_thread_wrapper(func)(self, *args, **kwargs)
        return func(self, *args, **kwargs)

    return wrapper
