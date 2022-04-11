# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.utils import set_property


class Line(QtWidgets.QFrame):
    def __init__(self, horizontal=True, style=None, parent=None):
        super(Line, self).__init__(parent=parent)
        if horizontal:
            self.setMaximumHeight(1)
            self.setMinimumHeight(1)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
            )
        else:
            self.setMaximumWidth(1)
            self.setMinimumWidth(1)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred
            )
        if style is not None:
            set_property(self, 'style', style)
