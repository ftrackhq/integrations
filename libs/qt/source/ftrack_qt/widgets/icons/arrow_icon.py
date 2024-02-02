# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.icons.status_icon import StatusMaterialIconWidget


class ArrowMaterialIconWidget(StatusMaterialIconWidget):
    '''Custom material icon widget for arrow, emitting event on click'''

    clicked = QtCore.Signal(object)

    def __init__(self, name, color=None, parent=None):
        super(ArrowMaterialIconWidget, self).__init__(
            name, color=color, parent=parent
        )

    def mousePressEvent(self, event):
        self.clicked.emit(event)
        return super(ArrowMaterialIconWidget, self).mousePressEvent(event)
