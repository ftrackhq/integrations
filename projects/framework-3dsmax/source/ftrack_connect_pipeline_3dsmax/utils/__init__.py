# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import threading
from functools import wraps
import shiboken2

from Qt import QtWidgets

from pymxs import runtime as rt


def run_in_main_thread(f):
    '''Make sure a function runs in the main Max thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            raise Exception(
                '3DS Max does not support multithreading, please revisit DCC implementation!'
            )
        else:
            return f(*args, **kwargs)

    return decorated


def get_main_window():
    '''Return the QMainWindow for the main Max window.'''
    main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
    main_window = shiboken2.wrapInstance(
        shiboken2.getCppPointer(main_window_qwdgt)[0], QtWidgets.QMainWindow
    )
    return main_window


def get_time_range():
    '''Return the start and end frame of the current scene'''
    start = rt.animationRange.start
    end = rt.animationRange.end
    return (start, end)


from ftrack_connect_pipeline_3dsmax.utils.bootstrap import *
from ftrack_connect_pipeline_3dsmax.utils.file import *
from ftrack_connect_pipeline_3dsmax.utils.node import *
