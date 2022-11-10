# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack
import threading
from functools import wraps

from ftrack_connect_pipeline.utils import (
    get_save_path,
)

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

def save(context_id, session, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    save_path, message = get_save_path(
        context_id, session, extension='.mb', temp=temp
    )

    if save_path is None:
        return (False, message)

    # Save Maya scene to this path
    #cmds.file(rename=save_path)
    if save:
        #cmds.file(save=True)
        message = 'Saved {{cookiecutter.host_type_capitalized}}  scene @ "{}"'.format(save_path)
    else:
        message = 'Renamed {{cookiecutter.host_type_capitalized}}  scene @ "{}"'.format(save_path)
    #if not temp:
        # Add to recent files
        #mm.eval("source addRecentFile;")
        #mm.eval(
        #    'addRecentFile("{}.mb","{}");'.format(
        #        save_path.replace('\\', '/'), 'mayaBinary'
        #    )
        #)

    result = save_path

    return result, message