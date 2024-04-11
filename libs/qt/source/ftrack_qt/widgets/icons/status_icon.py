# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
# TODO: clean this code
import logging

from Qt import QtCore, QtWidgets, QtGui, QtSvg

import ftrack_constants as constants
from ftrack_qt.widgets.icons import MaterialIcon

logger = logging.getLogger(__name__)


# This is the old materialIconWidget
class StatusMaterialIconWidget(QtWidgets.QWidget):
    '''Material icon widget, support status > icon encoding'''

    @property
    def icon(self):
        '''Return the material icon'''
        return self._icon

    def __init__(self, name, variant=None, color=None, parent=None):
        '''
        Initialize MaterialIconWidget

        :param name: The name of material icon SVG image
        :param color: The color, in html #RRGGBB format, or rgba(r,g,b,alpha)
        :param variant: The variant of material icon to use
        :param parent:  The parent dialog or frame
        '''
        super(StatusMaterialIconWidget, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(1)
        self._icon = None
        if name:
            self.set_icon(name, color=color, variant=variant)

    def set_icon(self, name, variant=None, color=None, size=16):
        '''Set the icon based on *name*, *variant*, *color* and *size*'''
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        if color is None:
            color = 'gray'
        label = QtWidgets.QLabel()
        self._icon = MaterialIcon(name, variant=variant, color=color)
        label.setPixmap(self._icon.pixmap(QtCore.QSize(size, size)))
        self.layout().addWidget(label)

    def set_status(self, status, size=16):
        '''Set the icon based on the pipeline *status*'''
        icon_name = ''
        color = '303030'
        variant = 'filled'
        if status in [
            constants.status.UNKNOWN_STATUS,
            constants.status.DEFAULT_STATUS,
        ]:
            icon_name = 'help'
            color = '303030'
        elif status in [constants.status.RUNNING_STATUS]:
            icon_name = 'hourglass_bottom'
            color = '87E1EB'
        elif status in [constants.status.SUCCESS_STATUS]:
            icon_name = 'check-circle-outline'
            color = '79DFB6'
        elif status in [constants.status.WARNING_STATUS]:
            icon_name = 'error_outline'
            color = 'FFBD5D'
        elif status in [
            constants.status.ERROR_STATUS,
            constants.status.EXCEPTION_STATUS,
        ]:
            icon_name = 'error'
            color = 'FF7A73'
        self.set_icon(
            icon_name, variant=variant, color='#{}'.format(color), size=size
        )
        return color
