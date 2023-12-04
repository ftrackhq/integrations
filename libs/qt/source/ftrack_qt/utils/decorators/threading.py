# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


def invoke_in_qt_main_thread(func):
    '''Decorator to ensure the function runs in the QT main thread.'''
    from Qt import QtCore, QtWidgets

    def wrapper(*args, **kwargs):
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

    return wrapper
