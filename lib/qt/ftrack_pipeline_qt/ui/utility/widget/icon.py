# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from Qt import QtCore, QtWidgets, QtGui, QtSvg

from ftrack_connect_pipeline import constants as core_constants

logger = logging.getLogger(__name__)


class MaterialIcon(QtGui.QIcon):
    '''Material icon, displaying SVG material icon images'''

    def __init__(self, name, color=None, variant=None, parent=None):
        '''
        Initialize the MaterialIcon

        :param name: The name of material icon SVG image
        :param color: The color, in html #RRGGBB format, or rgba(r,g,b,alpha)
        :param variant: The variant of material icon to use
        :param parent:  The parent dialog or frame
        '''
        self._name = name.replace('-', '_')
        self.color = color
        if variant is None:
            variant = 'filled'
        resource_path = ':ftrack/image/material-design-icons/{}/{}'.format(
            variant, self._name
        )
        pixmap = None
        if not color is None:
            # Read SVG and add fill color
            inFile = QtCore.QFile(resource_path)
            if inFile.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                text_stream = QtCore.QTextStream(inFile)
                svg_data = text_stream.readAll()
                svg_data = svg_data.replace(
                    '/></svg>', ' fill="{}"/></svg>'.format(color)
                )
                svg_renderer = QtSvg.QSvgRenderer(
                    QtCore.QByteArray(bytearray(svg_data.encode()))
                )
                pixmap = QtGui.QPixmap(svg_renderer.defaultSize())
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                svg_renderer.render(painter)
                painter.end()
            else:
                logger.warning(
                    'Unknown material icon resource: {}!'.format(resource_path)
                )
        else:
            pixmap = QtGui.QPixmap(resource_path)
            if pixmap is None or pixmap.isNull():
                logger.warning(
                    'Unknown material icon resource: {}!'.format(resource_path)
                )
        super(MaterialIcon, self).__init__(pixmap, parent=parent)


class MaterialIconWidget(QtWidgets.QWidget):
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
        super(MaterialIconWidget, self).__init__(parent=parent)
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
            core_constants.UNKNOWN_STATUS,
            core_constants.DEFAULT_STATUS,
        ]:
            icon_name = 'help'
            color = '303030'
        elif status in [core_constants.RUNNING_STATUS]:
            icon_name = 'hourglass_bottom'
            color = '87E1EB'
        elif status in [core_constants.SUCCESS_STATUS]:
            icon_name = 'check-circle-outline'
            color = '79DFB6'
        elif status in [core_constants.WARNING_STATUS]:
            icon_name = 'error_outline'
            color = 'FFBD5D'
        elif status in [
            core_constants.ERROR_STATUS,
            core_constants.EXCEPTION_STATUS,
        ]:
            icon_name = 'error'
            color = 'FF7A73'
        self.set_icon(
            icon_name, variant=variant, color='#{}'.format(color), size=size
        )
        return color
