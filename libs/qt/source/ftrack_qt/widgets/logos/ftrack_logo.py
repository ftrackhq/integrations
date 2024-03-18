# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


class FtrackLogo(QtWidgets.QLabel):
    '''Header logo widget'''

    def __init__(self, parent=None):
        '''Instantiate logo widget.'''
        super(FtrackLogo, self).__init__(parent=parent)

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

    def build(self):
        resource_path = ':ftrack/image/default/connectLogoDark'
        logoPixmap = QtGui.QPixmap(resource_path)
        if not logoPixmap is None:
            self.setPixmap(
                logoPixmap.scaled(
                    QtCore.QSize(106, 32),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.setPixmap(logoPixmap)
        else:
            self.setText("ftrack")
