# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui


class AssetVersionStatusWidget(QtWidgets.QFrame):
    '''Widget representing static asset state'''

    def __init__(self, bordered=True):
        super(AssetVersionStatusWidget, self).__init__()
        self._bordered = bordered

        self.pre_build()
        self.build()
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(4, 2, 4, 2)
        self.layout().setSpacing(4)

    def build(self):
        self._label_widget = QtWidgets.QLabel()
        if self._bordered:
            self._label_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(self._label_widget)

    def set_status(self, status):
        self._label_widget.setText(status['name'].upper())
        self._label_widget.setStyleSheet(
            '''
            color: {0};
            border: none;
        '''.format(
                status['color']
            )
        )
