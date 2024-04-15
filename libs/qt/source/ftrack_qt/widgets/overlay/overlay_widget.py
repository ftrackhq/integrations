# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


from ftrack_qt.widgets.icons import MaterialIcon


class OverlayWidget(QtWidgets.QFrame):
    '''
    Empty widget holder ready to parent a widget with a close button
    '''

    close_button_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        '''
        Initialize Overlay
        '''
        super(OverlayWidget, self).__init__(parent=parent)

        self._container_widget = None
        self._close_btn = None
        self._fill_color = None
        self._pen_color = None
        self._event_filter_installed = False

        self.build()
        self.post_build()

    def build(self):
        main_layout = QtWidgets.QVBoxLayout()

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addStretch()

        self._close_btn = QtWidgets.QPushButton('')
        self._close_btn.setIcon(MaterialIcon('close', color='#FFDD86'))
        self._close_btn.setProperty('borderless', True)
        self._close_btn.setFixedSize(24, 24)

        h_layout.addWidget(self._close_btn)

        main_layout.addLayout(h_layout)
        self.setLayout(main_layout)

    def post_build(self):
        self._close_btn.clicked.connect(self.on_close_button_callback)

    def on_close_button_callback(self):
        '''Emit a signal when close button is clicked'''
        self.close_button_clicked.emit()

    def set_widget(self, widget):
        '''Set the given *widget* into the main layout'''
        self.layout().addWidget(widget)
