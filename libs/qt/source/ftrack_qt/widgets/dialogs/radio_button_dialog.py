# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class RadioButtonDialog(QtWidgets.QDialog):
    '''Dialog to select item from multiple items found.'''

    @property
    def items(self):
        '''Return items of the dialog'''
        return self._items

    def __init__(self, items, parent=None):
        '''
        Initialize dialog
        '''
        super(RadioButtonDialog, self).__init__(parent=parent)

        self.setWindowTitle('Select Item')

        self._items = items

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)

    def build(self):
        '''Build widgets'''

        message = QtWidgets.QLabel('Multiple items found, please select one: ')
        self.layout.addWidget(message)

        self.radio_buttons = []
        self.button_group = QtWidgets.QButtonGroup(self)

        for item in self.items:
            radio_button = QtWidgets.QRadioButton(item)
            self.radio_buttons.append(radio_button)
            self.button_group.addButton(radio_button)
            self.layout.addWidget(radio_button)

        self.ok_button = QtWidgets.QPushButton('OK')

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.ok_button)

        self.layout.addLayout(self.button_layout)

    def post_build(self):
        self.ok_button.clicked.connect(self.accept)

    def selected_item(self):
        for radio_button in self.radio_buttons:
            if radio_button.isChecked():
                return radio_button.text()
        return None
