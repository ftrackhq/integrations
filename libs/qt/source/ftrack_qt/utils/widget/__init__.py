# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import shiboken2

from Qt import QtWidgets, QtCore, QtGui

# TODO: check this utilities if they are really needed.


def find_parent(widget, class_name):
    '''Recursively find upstream widget having class name
    containing *class_name*'''
    parent_widget = widget.parentWidget()
    if not parent_widget:
        return
    if parent_widget.__class__.__name__.find(class_name) > -1:
        return parent_widget
    return find_parent(parent_widget, class_name)


def get_main_window_from_widget(widget, class_name):
    '''This function will return the main window from the
    given *widget*.'''
    main_window = widget.window()
    if not main_window:
        return
    # Locate the topmost widget
    parent = find_parent(widget.parentWidget(), class_name)
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


def center_widget(widget, width=None, height=None):
    '''Returns a widget that is *widget* centered horizontally and vertically'''
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
