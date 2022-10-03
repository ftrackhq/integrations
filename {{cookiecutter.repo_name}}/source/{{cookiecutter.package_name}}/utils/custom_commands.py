# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack
import threading
from functools import wraps

def init_{{cookiecutter.host_type}}(context_id=None, session=None):
    '''
    Initialise timeline in {{cookiecutter.host_type_capitalized}} based on shot/asset build settings.

    :param session:
    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
    :return:
    '''
    pass

def get_main_window():
    """Return the QMainWindow for the main {{cookiecutter.host_type_capitalized}} window."""
    return None

def run_in_main_thread(f):
    '''Make sure a function runs in the main {{cookiecutter.host_type_capitalized}} thread.'''

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
