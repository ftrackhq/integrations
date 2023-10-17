# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtCore


class InvokeEvent(QtCore.QEvent):
    '''Event.'''

    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        '''Invoke *fn* in main thread.'''
        QtCore.QEvent.__init__(self, InvokeEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class Invoker(QtCore.QObject):
    '''Invoker.'''

    def event(self, event):
        '''Call function on *event*.'''
        event.fn(*event.args, **event.kwargs)

        return True


_invoker = Invoker()


def invoke_in_qt_thread(fn, *args, **kwargs):
    '''Invoke function *fn* with arguments.'''
    QtCore.QCoreApplication.postEvent(
        _invoker, InvokeEvent(fn, *args, **kwargs)
    )