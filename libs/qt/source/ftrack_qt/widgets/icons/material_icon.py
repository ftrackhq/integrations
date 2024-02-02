# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging

from Qt import QtCore, QtWidgets, QtGui, QtSvg


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

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

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
                self.logger.warning(
                    'Unknown material icon resource: {}!'.format(resource_path)
                )
        else:
            pixmap = QtGui.QPixmap(resource_path)
            if pixmap is None or pixmap.isNull():
                self.logger.warning(
                    'Unknown material icon resource: {}!'.format(resource_path)
                )
        super(MaterialIcon, self).__init__(pixmap, parent=parent)
