# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import threading
from functools import wraps

import maya.utils as maya_utils
import maya.OpenMayaUI as OpenMayaUI

from Qt import QtWidgets, QtCompat


def run_in_main_thread(f):
    '''Make sure a function runs in the main Maya thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated


def get_main_window():
    """Return the QMainWindow for the main Maya window."""
    winptr = OpenMayaUI.MQtUtil.mainWindow()
    if winptr is None:
        raise RuntimeError('No Maya window found.')
    window = QtCompat.wrapInstance(int(winptr))
    assert isinstance(window, QtWidgets.QMainWindow)
    return window


from ftrack_connect_pipeline_maya.utils.file import *
from ftrack_connect_pipeline_maya.utils.node import *
from ftrack_connect_pipeline_maya.utils.bootstrap import *
