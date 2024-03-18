# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore

    is_pyside6 = True
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

    is_pyside6 = False

from ftrack_qt.widgets.overlay import ShadedWidget

import ftrack_constants.qt as qt_constants
from ftrack_qt.utils.theme import apply_theme


class StyledDialog(QtWidgets.QDialog):
    '''
    The base dialog -intended to live docked, on top of DCC app main window or os
    a modal dialog in general.

    To be inherited by publisher, assembler and other dialogs.

    Designed to become shaded when another (modal) dialog is put in front of it,
    for visibility.
    '''

    DEFAULT_STYLE = qt_constants.theme.DEFAULT_STYLE

    # Allow child classes to override the default theme and background style
    theme = qt_constants.theme.DEFAULT_THEME
    background_style = qt_constants.theme.DEFAULT_BACKGROUND_STYLE

    @property
    def darken(self):
        return self._darken

    @darken.setter
    def darken(self, value):
        self._darken = value
        if self._darken:
            self._shaded_widget = ShadedWidget(self)
            self._shaded_widget.move(0, 0)
            self._shaded_widget.resize(self.size())
            self._shaded_widget.show()
        else:
            if self._shaded_widget:
                self._shaded_widget.close()

    def __init__(self, background_style=None, docked=False, parent=None):
        super(StyledDialog, self).__init__(parent=parent)
        self._darken = False
        self._shaded_widget = None

        if background_style:
            self.background_style = background_style

        self.docked = docked

        # Apply theme and with DCC specific properties
        # TODO: This has been deactivated as it makes the filebrowser dialog
        #  crash after selecting a file. If this needs to be activated in the
        #  future for DCC reasons: 1- Double check file browser dialog still
        #  working after selecting a file in standalone ui mode. 2- if not
        #  working, find another way to simulate the tool property in PySide2.
        #  Tool property documentation:
        #  https://doc.qt.io/qtforpython-5/PySide2/QtCore/Qt.html#:~:text=Qt.Tool-,Indicates,-that%20the%20widget
        #  probably the reason of the crashing remains in here: " This means that
        #  the window lives on a level above normal windows making it impossible
        #  to put a normal window on top of it. By default, tool windows will
        #  disappear when the application is inactive. This can be controlled by
        #  the WA_MacAlwaysShowToolWindow attribute. "
        # self.setWindowFlags(QtCore.Qt.Tool)

        self.setSizeGripEnabled(True)  # Enable resize on Windows

        apply_theme(self, self.theme)
        self.setProperty('background', self.background_style)
        self.setProperty('docked', 'true' if self.docked else 'false')

        if is_pyside6:
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
            # Make sure the dialog is always on top
            self.setWindowFlags(QtCore.Qt.WidgetAttribute.WindowStaysOnTopHint)
        else:
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            # Make sure the dialog is always on top
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # Have a proper title instead of default 'python'
        self.setWindowTitle('ftrack')
