# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


try:
    from PySide6 import QtWidgets, QtCore, QtGui
    import shiboken6 as shiboken
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    import shiboken2 as shiboken

from ftrack_utils.framework.config.tool import get_plugins


def check_framework_dialog_bases(cls):
    '''Recursively check the base classes for FrameworkDialog.'''
    for base in cls.__bases__:
        if base.__name__ == 'FrameworkDialog':
            return base
        if check_framework_dialog_bases(base):
            return base
    return False


def get_main_window_from_widget(widget):
    '''Return the main window from the given widget.'''
    return widget.window()


def get_framework_main_dialog(widget):
    '''Return the main Framework dialog from the given widget.'''
    main_dialog = None
    while not main_dialog:
        widget = widget.parentWidget()
        if not widget:
            break
        if check_framework_dialog_bases(widget.__class__):
            main_dialog = widget

    return main_dialog


def set_property(widget, name, value):
    '''Update property *name* to *value* for *widget*, and polish afterwards.'''
    widget.setProperty(name, value)
    if widget.style() is not None and shiboken.isValid(
        widget.style()
    ):  # Only update style if applied and valid
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    widget.update()


def set_properties(widget, properties):
    """
    Set multiple properties on a Qt widget.

    Args:
        widget (QWidget): The widget on which to set the properties.
        properties (dict): A dictionary of property names and values.
    """
    for name, value in properties.items():
        widget.setProperty(name, value)
        if widget.style() is not None and shiboken.isValid(
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


def build_progress_data(tool_config):
    '''Build progress data from *tool_config*'''
    progress_data = []
    for plugin_config in get_plugins(tool_config, with_parents=True):
        phase_data = {
            'id': plugin_config['reference'],
            'label': plugin_config['plugin'].replace('_', ' ').title(),
        }
        tags = plugin_config.get('tags') or []
        for group in plugin_config.get('parents') or []:
            if 'options' in group:
                tags.extend(list(str(group['options'].values())))
            if 'tags' in group:
                tags.extend(group['tags'])
        phase_data['tags'] = reversed(tags)
        progress_data.append(phase_data)
    return progress_data
