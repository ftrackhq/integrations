# :coding: utf-8
# :copyright: Copyright (c) 2019-2022 ftrack

import threading
import sys
import logging
import contextlib
import shiboken2

import ftrack_api

from Qt import QtCore, QtWidgets, QtGui

from ftrack_connect_pipeline_qt.ui import theme
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
            '''Wrap method and pass exceptions to global excepthook.

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
    '''Thread helper class providing callback functionality'''

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


def is_main_thread():
    '''Return True if running in main thread.'''
    return (
        QtCore.QThread.currentThread()
        == QtCore.QCoreApplication.instance().thread()
    )


def get_theme():
    '''Return the theme, return None to disable themes. Can be overridden by child.'''
    return 'dark'


def set_theme(widget, selected_theme):
    '''Set the widget theme'''
    theme.applyTheme(widget, selected_theme)


def find_parent(widget, class_name):
    '''Recursively find upstream widget having class name
    containing *class_name*'''
    parent_widget = widget.parentWidget()
    if not parent_widget:
        return
    if parent_widget.__class__.__name__.find(class_name) > -1:
        return parent_widget
    return find_parent(parent_widget, class_name)


def get_main_framework_window_from_widget(widget):
    '''This function will return the main window of the framework from the
    given *widget*. The main window is named as main_framework_widget'''
    main_window = widget.window()
    if not main_window:
        return
    # Locate the topmost framework(client) widget
    parent = find_parent(widget.parentWidget(), qt_constants.CLIENT_WIDGET)
    if parent:
        main_window = parent

    return main_window


def set_property(widget, name, value):
    '''Update property *name* to *value* for *widget*, and polish afterwards.'''
    widget.setProperty(name, value)
    if widget.style() is not None and shiboken2.isValid(
        widget.style()
    ):  # Only update style if applied and valid
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    widget.update()


def clear_layout(layout):
    '''Recursively remove all widgets from the *layout*'''
    while layout is not None and layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            clear_layout(item.layout())


def center_widget(widget, width=None, height=None):
    '''Returns a widget that is have *widget* centered horizontally and vertically'''
    v_container = QtWidgets.QWidget()
    v_container.setLayout(QtWidgets.QVBoxLayout())
    v_container.layout().addWidget(QtWidgets.QLabel(""), 100)

    h_container = QtWidgets.QWidget()
    h_container.setLayout(QtWidgets.QHBoxLayout())
    h_container.layout().addWidget(QtWidgets.QLabel(), 100)
    h_container.layout().addWidget(widget)
    if not width is None and not height is None:
        widget.setMaximumSize(QtCore.QSize(width, height))
        widget.setMinimumSize(QtCore.QSize(width, height))
    h_container.layout().addWidget(QtWidgets.QLabel(), 100)
    v_container.layout().addWidget(h_container)

    v_container.layout().addWidget(QtWidgets.QLabel(), 100)
    return v_container


class FilterClass(QtCore.QObject):
    '''Filter class to be used with the input event blocker below'''

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
    '''Conditional input event blocking widget'''

    def __init__(self, blocker, parent=None):
        '''
        Initialize InputEventBlockingWidget

        :param blocker: Blocker function that should return true if event should be blocked
        :param parent: The parent dialog or frame
        '''
        super(InputEventBlockingWidget, self).__init__(parent=parent)
        self._blocker = blocker
        self._filtered_widget = QtCore.QCoreApplication.instance()
        self._filtered_widget.installEventFilter(self)

    def stop(self):
        self._filtered_widget.removeEventFilter(self)

    def eventFilter(self, obj, event):
        '''Block *event* on *obj* while if blocker returns True'''
        retval = False
        if self._blocker() and (isinstance(event, QtGui.QInputEvent)):
            retval = True
        return retval
