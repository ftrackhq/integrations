# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import threading
from functools import wraps

import shiboken2

from pymxs import runtime as rt

from Qt import QtWidgets

from ftrack_connect_pipeline.utils import (
    get_save_path,
)


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
    main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
    main_window = shiboken2.wrapInstance(
        shiboken2.getCppPointer(main_window_qwdgt)[0], QtWidgets.QMainWindow
    )
    return main_window


def run_in_main_thread(f):
    '''Make sure a function runs in the main Max thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            # return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
            pass
        else:
            return f(*args, **kwargs)

    return decorated


def open_file(path, options):
    '''Native open file function'''
    # return cmds.file(path, o=True, f=True)


def import_file(path, options):
    '''Native import file function'''
    # return cmds.file(path, o=True, f=True)


def reference_file(path, options):
    '''Native reference file function'''
    # return cmds.file(path, o=True, f=True)


def save_file(save_path, context_id=None, session=None, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    # Max has no concept of renaming a scene, always save
    save = True

    if save_path is None:
        if context_id is not None and session is not None:
            # Attempt to find out based on context
            save_path, message = get_save_path(
                context_id, session, extension='.max', temp=temp
            )

            if save_path is None:
                return (False, message)
        else:
            return (
                False,
                'No context and/or session provided to generate save path',
            )

    if save:
        rt.savemaxFile(save_path, useNewFile=False)
        message = 'Saved Max scene @ "{}"'.format(save_path)
    else:
        raise Exception('Max scene rename not supported')

    result = save_path

    return result, message
