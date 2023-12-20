# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtCore, QtWidgets


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


class Invoker(QtCore.QObject):
    '''Invoker.'''

    def event(self, event):
        '''Call function on *event*.'''
        event.fn(*event.args, **event.kwargs)

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
        fn(*args, **kwargs)
    else:
        QtCore.QCoreApplication.postEvent(
            _invoker, InvokeEvent(fn, *args, **kwargs)
        )
