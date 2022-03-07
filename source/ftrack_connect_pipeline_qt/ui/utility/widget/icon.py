# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets, QtGui, QtSvg

from ftrack_connect_pipeline_qt import constants


class MaterialIcon(QtGui.QIcon):
    def __init__(self, name, color=None, variant=None, parent=None):
        self._name = name.replace('-', '_')
        self.color = color
        if variant is None:
            variant = 'filled'
        resource_path = ':ftrack/image/material-design-icons/{}/{}'.format(
            variant, self._name
        )
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
                raise Exception(
                    'Unknown material icon resource: {}!'.format(resource_path)
                )
        else:
            pixmap = QtGui.QPixmap(resource_path)
            if pixmap is None or pixmap.isNull():
                raise Exception(
                    'Unknown material icon resource: {}!'.format(resource_path)
                )
        if color is not None and False:
            # Colorize it
            mask = pixmap.scaled(
                QtCore.QSize(512, 512),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            ).createMaskFromColor(
                QtGui.QColor(0, 0, 0), QtCore.Qt.MaskOutColor
            )
            pixmap = QtGui.QPixmap(QtCore.QSize(512, 512))
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setPen(QtGui.QColor(color))
            painter.drawPixmap(pixmap.rect(), mask, mask.rect())
            painter.end()
            # pixmap.setMask(mask)
        # engine = MaterialIconEngine(pixmap)
        super(MaterialIcon, self).__init__(pixmap, parent=parent)


class MaterialIconWidget(QtWidgets.QWidget):
    @property
    def icon(self):
        return self._icon

    def __init__(self, name, parent=None, color=None):
        super(MaterialIconWidget, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(1)
        self._icon = None
        if name:
            self.set_icon(name, color=color)

    def set_icon(self, name, variant=None, color=None, size=16):
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        if color is None:
            color = 'gray'
        label = QtWidgets.QLabel()
        self._icon = MaterialIcon(name, variant=variant, color=color)
        label.setPixmap(self._icon.pixmap(QtCore.QSize(size, size)))
        self.layout().addWidget(label)

    def set_status(self, status, size=16):
        icon_name = ''
        color = '303030'
        variant = 'filled'
        if status in [constants.UNKNOWN_STATUS, constants.DEFAULT_STATUS]:
            icon_name = 'help'
            color = '303030'
        elif status in [constants.RUNNING_STATUS]:
            icon_name = 'loading'
            color = '87E1EB'
        elif status in [constants.SUCCESS_STATUS]:
            icon_name = 'check-circle-outline'
            color = '79DFB6'
        elif status in [constants.WARNING_STATUS]:
            icon_name = 'error_outline'
            color = 'FFBD5D'
        elif status in [constants.ERROR_STATUS, constants.EXCEPTION_STATUS]:
            icon_name = 'error'
            color = 'FF7A73'
        self.set_icon(
            icon_name, variant=variant, color='#{}'.format(color), size=size
        )
        return color
