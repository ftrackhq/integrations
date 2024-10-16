# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import threading
from functools import wraps


def run_in_main_thread(f):
    '''Make sure a function runs in the main Flame thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            pass
            # return flame_utils.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated
