# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from ftrack_qt.utils.widget import set_property


class NewAssetInput(QtWidgets.QFrame):
    '''Widget holding new asset input during publish'''

    active_changed = QtCore.Signal(object)
    '''Signal emitted when the input is activated or deactivated, with active as argument.'''

    text_changed = QtCore.Signal(object)
    '''Signal emitted when the text is changed, with text as argument.'''

    @property
    def active(self):
        '''Return whether the input is active.'''
        return self._active

    @active.setter
    def active(self, value):
        '''Set the input as active or inactive.'''
        if self._active == value:
            return
        self._active = value
        self._button.setEnabled(not value)
        self._name.setVisible(value)
        self._version_label.setVisible(value)
        self._filler.setVisible(not value)
        self._button.setEnabled(not value)
        if value:
            self._name.setFocus()
            self.text_changed.emit(self._name.text())
        self.active_changed.emit(value)

    def __init__(self, validator, placeholder_name):
        '''Initialize the NewAssetInput widget.'''
        super(NewAssetInput, self).__init__()

        self._validator = validator
        self._placeholder_name = placeholder_name
        self._active = False

        self._button = None
        self._name = None
        self._version_label = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Set up layout and dimensions before building.'''
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(4, 1, 1, 1)
        self.layout().setSpacing(1)
        self.setMaximumHeight(32)

    def build(self):
        '''Build the button, name input, and version label.'''
        self._button = QtWidgets.QPushButton('NEW')
        self._button.setStyleSheet('background: #FFDD86;')
        self._button.setFixedSize(56, 30)
        self._button.setMaximumSize(56, 30)

        self.layout().addWidget(self._button)

        self._name = QtWidgets.QLineEdit()
        self._name.setPlaceholderText(self._placeholder_name)
        self._name.setValidator(self._validator)
        self._name.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self._name.setVisible(False)
        self.layout().addWidget(self._name, 1000)

        self._version_label = QtWidgets.QLabel('- Version 1')
        self._version_label.setObjectName('color-primary')
        self._version_label.setVisible(False)
        self.layout().addWidget(self._version_label)

        self._filler = QtWidgets.QLabel('')
        self._filler.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.layout().addWidget(self._filler, 100)

    def post_build(self):
        '''Connect signals and callbacks after building.'''
        self._button.clicked.connect(self.input_clicked)
        self._name.mousePressEvent = self.input_clicked
        self._name.textChanged.connect(self.on_text_changed)

    def mousePressEvent(self, event):
        '''Override mouse press to emit signal.'''
        super(NewAssetInput, self).mousePressEvent(event)
        self.active = True
        self.text_changed.emit(self._name.text())

    def input_clicked(self, event):
        '''Callback on user button or name click.'''
        self.active = True
        self.text_changed.emit(self._name.text())

    def on_text_changed(self):
        '''Emit signal when text is changed.'''
        self.text_changed.emit(self._name.text())

    def set_valid(self, valid):
        '''Set the input field as valid or invalid.'''
        if valid:
            set_property(self._name, 'input', '')
        else:
            set_property(self._name, 'input', 'invalid')

    def set_default_name(self, name):
        '''Set the default name for the input field.'''
        self._name.setText(name)
