# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import threading
from functools import wraps

import nuke

from Qt import QtWidgets


def get_main_window():
    '''Return the main Nuke window.'''
    return QtWidgets.QApplication.activeWindow()


def run_in_main_thread(f):
    '''Make sure a function runs in the main Nuke thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return nuke.executeInMainThreadWithResult(
                f, args=args, kwargs=kwargs
            )
        else:
            return f(*args, **kwargs)

    return decorated


from ftrack_connect_pipeline_nuke.utils.node import *
from ftrack_connect_pipeline_nuke.utils.file import *
from ftrack_connect_pipeline_nuke.utils.bootstrap import *
