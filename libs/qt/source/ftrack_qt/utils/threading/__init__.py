# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtCore, QtWidgets


class InvokeEvent(QtCore.QEvent):
    '''Event.'''

    def __init__(self, fn, *args, **kwargs):
        '''Invoke *fn* in main thread.'''
        QtCore.QEvent.__init__(
            self, QtCore.QEvent.Type(QtCore.QEvent.registerEventType(self))
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


def invoke_in_qt_thread(fn, *args, **kwargs):
    '''Invoke function *fn* with arguments.'''
    QtCore.QCoreApplication.postEvent(
        _invoker, InvokeEvent(fn, *args, **kwargs)
    )


def invoke_in_qt_main_thread(func, *args, **kwargs):
    '''Decorator to ensure the function runs in the QT main thread.'''
    if (
        QtCore.QThread.currentThread()
        != QtWidgets.QApplication.instance().thread()
    ):
        QtCore.QMetaObject.invokeMethod(
            QtWidgets.QApplication.instance(),
            func.__name__,
            QtCore.Qt.QueuedConnection,
        )
    else:
        return func(*args, **kwargs)
