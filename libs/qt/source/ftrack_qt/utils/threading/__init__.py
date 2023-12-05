# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtCore, QtWidgets


def invoke_in_qt_main_thread(func, *args, **kwargs):
    '''Decorator to ensure the function runs in the QT main thread.'''
    print("yay")
    if (
        QtCore.QThread.currentThread()
        != QtWidgets.QApplication.instance().thread()
    ):
        print("not main thread")
        QtCore.QMetaObject.invokeMethod(
            QtWidgets.QApplication.instance(),
            func.__name__,
            QtCore.Qt.QueuedConnection,
        )
    else:
        print("main thread")
        return func(*args, **kwargs)
