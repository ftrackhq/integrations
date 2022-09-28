# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import threading
from functools import wraps

def init_max(context_id=None, session=None):
    '''
    Initialise timeline in Max based on shot/asset build settings.

    :param session:
    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
    :return:
    '''
    pass

def get_main_window():
    """Return the QMainWindow for the main Max window."""
    return None

def run_in_main_thread(f):
    '''Make sure a function runs in the main Max thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            #return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
            pass
        else:
            return f(*args, **kwargs)

    return decorated

def open_file(path, options):
    '''Native open file function '''
    # return cmds.file(path, o=True, f=True)

def import_file(path, options):
    '''Native import file function '''
    # return cmds.file(path, o=True, f=True)

def reference_file(path, options):
    '''Native reference file function '''
    # return cmds.file(path, o=True, f=True)