# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore

    is_pyside6 = True
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

    is_pyside6 = False

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
                QtWidgets.QSizePolicy.Policy.Preferred
                if is_pyside6
                else QtWidgets.QSizePolicy.Preferred,
                QtWidgets.QSizePolicy.Policy.Minimum
                if is_pyside6
                else QtWidgets.QSizePolicy.Minimum,
            )
        else:
            self.setMaximumWidth(1)
            self.setMinimumWidth(1)
            self.setMaximumHeight(16)
            self.setMinimumHeight(16)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Minimum
                if is_pyside6
                else QtWidgets.QSizePolicy.Minimum,
                QtWidgets.QSizePolicy.Policy.Preferred
                if is_pyside6
                else QtWidgets.QSizePolicy.Preferred,
            )
        if style is not None:
            set_property(self, 'style', style)
