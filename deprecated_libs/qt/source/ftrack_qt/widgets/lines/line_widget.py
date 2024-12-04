# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.utils.widget import set_property


class LineWidget(QtWidgets.QFrame):
    '''Widget presenting a one pixel wide line'''

    def __init__(self, horizontal=True, style=None, parent=None):
        '''
        Initialize Line

        :param horizontal: Line orientation
        :param style: The CSS style
        :param parent: The parent dialog or frame
        '''
        super(LineWidget, self).__init__(parent=parent)

        if horizontal:
            self.setMaximumHeight(1)
            self.setMinimumHeight(1)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Preferred,
                QtWidgets.QSizePolicy.Policy.Minimum,
            )
        else:
            self.setMaximumWidth(1)
            self.setMinimumWidth(1)
            self.setMaximumHeight(16)
            self.setMinimumHeight(16)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Preferred,
            )
        if style is not None:
            set_property(self, 'style', style)
