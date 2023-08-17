from Qt import QtWidgets, QtCore


class BrowseWidget(QtWidgets.QWidget):
    '''Browse Widget is a line edit with a browse button'''

    browse_button_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        '''
        Initialize Browse widget
        '''
        super(BrowseWidget, self).__init__(parent=parent)

        self.build()
        self.post_build()

    def build(self):
        '''Build widgets'''
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(15, 0, 0, 0)
        self.layout().setSpacing(0)

        self._path_le = QtWidgets.QLineEdit()

        self.layout().addWidget(self._path_le, 20)

        self._browse_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_btn.setObjectName('borderless')

        self.layout().addWidget(self._browse_btn)

    def post_build(self):
        '''Connect widget signals'''
        self._browse_btn.clicked.connect(self._browse_button_clicked)

    def get_path(self):
        '''Get path from the line edit'''
        return self._path_le.text()

    def set_path(self, path_text):
        '''Set path to the line edit'''
        self._path_le.setText(path_text)

    def set_tool_tip(self, tooltip_text):
        '''Set tooltip'''
        self._path_le.setToolTip(tooltip_text)

    def _browse_button_clicked(self):
        '''Browse button clicked signal'''
        self.browse_button_clicked.emit()
