# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import threading
from functools import wraps

from typing import Callable

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import QObject, Signal, Slot
    from PySide6.QtGui import QGuiApplication
except ImportError:
    from PySide2 import QtCore, QtGui
    from PySide2.QtCore import QObject, Signal, Slot
    from PySide2.QtGui import QtWidgets, QGuiApplication

import qtmax

# Dock widget in Max
def dock_max_right(widget):
    '''Dock *widget* to the right side of Max.'''
    # Use the current widget's parent as the parent for the dockable
    # widget

    dock_widget = QtWidgets.QDockWidget()
    dock_widget.setWindowTitle(widget.windowTitle())
    dock_widget.setObjectName(widget.windowTitle())
    dock_widget.setWidget(widget)
    qtmax.GetQMaxMainWindow().addDockWidget(
        QtCore.Qt.RightDockWidgetArea,
        dock_widget,
        QtCore.Qt.Horizontal
    )
    dock_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
    dock_widget.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    dock_widget.setFloating(False)
    dock_widget.show()


def run_in_main_thread(f):
    '''Make sure a function runs in the main Max thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.current_thread().name != 'MainThread':
            return ExecuteInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated


class ExecuteInMainThreadWithResult(QObject):
    def __init__(self, method: Callable, *args, **kwargs):
        '''Invokes a method on the main thread. Taking care of garbage collection "bugs".'''
        super().__init__()

        main_thread = QGuiApplication.instance().thread()
        self.moveToThread(main_thread)
        self.setParent(QGuiApplication.instance())
        self.method_with_args = (method, args, kwargs)
        self.called.connect(self.execute)
        self.called.emit()

    called = Signal()

    @Slot()
    def execute(self):
        result = self.method_with_args[0](
            *self.method_with_args[1], **self.method_with_args[2]
        )
        # trigger garbage collector
        self.setParent(None)
        return result
