# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import sys

from Qt import QtCore, QtWidgets


class Worker(QtCore.QThread):
    '''Perform work in a background thread.'''

    def __init__(self, function, args=None, kwargs=None, parent=None):
        '''Execute *function* in separate thread.

        *args* should be a list of positional arguments and *kwargs* a
        mapping of keyword arguments to pass to the function on execution.

        Store function call as self.result. If an exception occurs
        store as self.error.

        Example::

            try:
                worker = Worker(theQuestion, [42])
                worker.start()

                while worker.isRunning():
                    app = QtGui.QApplication.instance()
                    app.processEvents()

                if worker.error:
                    raise worker.error[1], None, worker.error[2]

            except Exception as error:
                traceback.print_exc()
                QtGui.QMessageBox.critical(
                    None,
                    'Error',
                    'An unhandled error occurred:'
                    '\\n{0}'.format(error)
                )

        '''
        super(Worker, self).__init__(parent=parent)
        self.setObjectName(str(function))
        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self.result = None
        self.error = None

    def run(self):
        '''Execute function and store result.'''
        try:
            self.result = self.function(*self.args, **self.kwargs)
        except Exception:
            self.error = sys.exc_info()


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
