# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.overlay import OverlayWidget


class BaseDialog(QtWidgets.QDialog):
    '''
    A basic dialog window, intended to live on top of DCC app main window (assembler, change context, entity browser,..)
    Becomes shaded when a modal dialog is put in front of it.
    '''

    @property
    def darken(self):
        return self._darken

    @darken.setter
    def darken(self, value):
        self._darken = value
        if self._darken:
            self._overlay_widget = OverlayWidget(self)
            self._overlay_widget.move(0, 0)
            self._overlay_widget.resize(self.size())
            self._overlay_widget.show()
        else:
            if self._overlay_widget:
                self._overlay_widget.close()

    def __init__(self, parent):
        super(BaseDialog, self).__init__(parent=parent)
        self._overlay_widget = None

