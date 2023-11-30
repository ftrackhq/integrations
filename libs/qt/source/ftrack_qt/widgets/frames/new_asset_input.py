# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui
from ftrack_qt.utils.widget import set_property


class NewAssetInput(QtWidgets.QFrame):
    '''Widget holding new asset input during publish'''

    text_changed = QtCore.Signal(object)

    def __init__(self, validator, placeholder_name):
        super(NewAssetInput, self).__init__()

        self._validator = validator
        self._placeholder_name = placeholder_name

        self._button = None
        self._name = None
        self._version_label = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(4, 1, 1, 1)
        self.layout().setSpacing(1)
        self.setMaximumHeight(32)

    def build(self):
        self._button = QtWidgets.QPushButton('NEW')
        self._button.setStyleSheet('background: #FFDD86;')
        self._button.setFixedSize(56, 30)
        self._button.setMaximumSize(56, 30)

        self.layout().addWidget(self._button)

        self._name = QtWidgets.QLineEdit()
        self._name.setPlaceholderText(self._placeholder_name)
        self._name.setValidator(self._validator)
        self._name.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
        )
        self.layout().addWidget(self._name, 1000)

        self._version_label = QtWidgets.QLabel('- Version 1')
        self._version_label.setObjectName("color-primary")
        self.layout().addWidget(self._version_label)

    def post_build(self):
        self._button.clicked.connect(self.input_clicked)
        self._name.mousePressEvent = self.input_clicked
        self._name.textChanged.connect(self.on_text_changed)

    def mousePressEvent(self, event):
        '''Override mouse press to emit signal'''
        self.text_changed.emit(self._name.text())

    def input_clicked(self, event):
        '''Callback on user button or name click'''
        self.text_changed.emit(self._name.text())

    def on_text_changed(self):
        self.text_changed.emit(self._name.text())

    def set_valid(self, valid):
        if valid:
            set_property(self._name, 'input', '')
        else:
            set_property(self._name, 'input', 'invalid')

    def set_default_name(self, name):
        self._name.setText(name)
