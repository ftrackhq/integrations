# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import threading
from functools import wraps


# Dock widget in Max
def dock_max_right(widget):
    '''Dock *widget* to the right side of Max.'''
    pass


def run_in_main_thread(f):
    '''Make sure a function runs in the main Max thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            pass
            # return max_utils.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated
