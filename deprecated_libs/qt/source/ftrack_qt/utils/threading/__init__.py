# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import time

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtWidgets


class InvokeEvent(QtCore.QEvent):
    '''Event.'''

    def __init__(self, fn, *args, **kwargs):
        '''Invoke *fn* in main thread.'''
        QtCore.QEvent.__init__(
            self, QtCore.QEvent.Type(QtCore.QEvent.registerEventType())
        )
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.triggered = False


class Invoker(QtCore.QObject):
    '''Invoker.'''

    def event(self, event):
        '''Call function on *event*.'''
        event.result = event.fn(*event.args, **event.kwargs)
        event.triggered = True
        return True


_invoker = Invoker(None)


def invoke_in_qt_main_thread(fn, *args, **kwargs):
    '''
    Invoke function *fn* with arguments, if not running in the main thread.

    TODO: Align this with DCC utility functions to run in main thread, and use them
    instead as their QT implementation might differ and this solution might not apply
    or cause instabilities.
    '''
    if QtCore.QThread.currentThread() is _invoker.thread():
        return fn(*args, **kwargs)
    else:
        invoke_event = InvokeEvent(fn, *args, **kwargs)
        QtCore.QCoreApplication.postEvent(_invoker, invoke_event)
        # Wait for event to be run
        while not invoke_event.triggered:
            time.sleep(0.01)
            QtWidgets.QApplication.processEvents()
        return invoke_event.result
