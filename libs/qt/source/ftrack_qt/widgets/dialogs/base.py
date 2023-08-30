# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.overlay import ShadedWidget

from ftrack_constants.qt.theme import DEFAULT_BACKGROUND_STYLE
from ftrack_qt.utils.theme import apply_theme

class StyledDialog(QtWidgets.QDialog):
    '''
    The base dialog -intended to live docked, on top of DCC app main window or os
    a modal dialog in general.

    To be inherited by publisher, assembler and other dialogs.

    Designed to become shaded when another (modal) dialog is put in front of it,
    for visibility.
    '''

    DEFAULT_STYLE = 'ftrack'

    # Allow child classes to override the default theme and background style
    theme = None
    background_style = None

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

    def __init__(self, theme=None, background_style=None, docked=False, parent=None):
        super(StyledDialog, self).__init__(parent=parent)
        self._darken = False
        self._shaded_widget = None

        # Apply theme and with DCC specific properties
        self.setWindowFlags(QtCore.Qt.Tool)
        apply_theme(self, theme=theme or self.theme)
        self.setProperty('background', background_style or self.background_style or
                         DEFAULT_BACKGROUND_STYLE)
        self.setProperty('docked', 'true' if docked else 'false')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

