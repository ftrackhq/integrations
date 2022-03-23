# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading
import sys
import logging
import contextlib

from Qt import QtCore, QtWidgets, QtGui

from ftrack_connect_pipeline_qt import constants as qt_constants


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

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self.result = None
        self.error = None

    def run(self):
        '''Execute function and store result.'''
        try:
            self.result = self.function(*self.args, **self.kwargs)
        except Exception as error:
            self.logger.error(str(error))
            self.error = sys.exc_info()


def asynchronous(method):
    '''Decorator to make a method asynchronous using its own thread.'''

    def wrapper(*args, **kwargs):
        '''Thread wrapped method.'''

        def exceptHookWrapper(*args, **kwargs):
            '''Wrapp method and pass exceptions to global excepthook.

            This is needed in threads because of
            https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470
            '''
            try:
                method(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info())

        thread = threading.Thread(
            target=exceptHookWrapper, args=args, kwargs=kwargs
        )
        thread.start()

    return wrapper


class BaseThread(threading.Thread):
    def __init__(self, callback=None, target_args=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(
            target=self.target_with_callback, *args, **kwargs
        )
        self.callback = callback
        self.method = target
        self.target_args = target_args

    def target_with_callback(self):
        result = self.method(*self.target_args)
        if self.callback is not None:
            self.callback(result)


def find_parent(widget, name):
    parent_widget = widget.parentWidget()
    if not parent_widget:
        return
    if name in parent_widget.objectName():
        return parent_widget
    return find_parent(parent_widget, name)


def get_main_framework_window_from_widget(widget):
    '''This function will return the main window of the framework from the
    given *widget*. The main window is named as main_framework_widget'''
    main_window = widget.window()
    if not main_window:
        return

    if qt_constants.MAIN_FRAMEWORK_WIDGET not in main_window.objectName():
        parent = find_parent(
            widget.parentWidget(), qt_constants.MAIN_FRAMEWORK_WIDGET
        )
        if parent:
            main_window = parent

    return main_window


def set_property(widget, name, value):
    '''Update property *name* to *value* for *widget*, and polish afterwards.'''
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def clear_layout(layout):
    while layout is not None and layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            clear_layout(item.layout())


def center_widget(w, width=None, height=None):
    v_container = QtWidgets.QWidget()
    v_container.setLayout(QtWidgets.QVBoxLayout())
    v_container.layout().addWidget(QtWidgets.QLabel(""), 100)

    h_container = QtWidgets.QWidget()
    h_container.setLayout(QtWidgets.QHBoxLayout())
    h_container.layout().addWidget(QtWidgets.QLabel(), 100)
    h_container.layout().addWidget(w)
    if not width is None and not height is None:
        w.setMaximumSize(QtCore.QSize(width, height))
        w.setMinimumSize(QtCore.QSize(width, height))
    h_container.layout().addWidget(QtWidgets.QLabel(), 100)
    v_container.layout().addWidget(h_container)

    v_container.layout().addWidget(QtWidgets.QLabel(), 100)
    return v_container


class FilterClass(QtCore.QObject):
    def __init__(self, blocker, parent=None):
        super(FilterClass, self).__init__(parent=parent)
        self._blocker = blocker

    def eventFilter(self, obj, event):
        '''Suppress all events.'''
        retval = False
        if self._blocker() and (isinstance(event, QtGui.QInputEvent)):
            retval = True
        return retval


@contextlib.contextmanager
def block_input_events(widget=None, blocker=None):
    '''Suppress any QT events during execution of this context (with clause).'''

    def always_block():
        return True

    filterObj = FilterClass(blocker or always_block)

    if widget is None:
        widget = QtCore.QCoreApplication.instance()
    widget.installEventFilter(filterObj)
    yield
    widget.removeEventFilter(filterObj)


class InputEventBlockingWidget(QtWidgets.QWidget):
    '''Conditional input event blocking widget.'''

    def __init__(self, blocker, parent=None):
        super(InputEventBlockingWidget, self).__init__(parent=parent)
        self._blocker = blocker
        application = QtCore.QCoreApplication.instance()
        application.installEventFilter(self)

    def eventFilter(self, obj, event):
        retval = False
        if self._blocker() and (isinstance(event, QtGui.QInputEvent)):
            retval = True
        return retval
