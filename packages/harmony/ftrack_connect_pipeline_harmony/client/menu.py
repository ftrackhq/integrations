# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog, icon

from ftrack_connect_pipeline_harmony import utils as harmony_utils


class HarmonyQtMenuClientWidget(dialog.ModalDialog):
    '''Harmony menu client - displays a modal menu with a list of actions.'''

    def __init__(self, widgets, app, event_pipeline_data, parent=None):
        self._widgets = widgets
        self._app = app
        self._event_pipeline_data = event_pipeline_data

        super(HarmonyQtMenuClientWidget, self).__init__(parent=parent)

        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        self.setProperty('docked', 'false')

        self.resize(170, 180)

        if (
            'x' in self._event_pipeline_data
            and 'y' in self._event_pipeline_data
        ):
            self.move(
                self._event_pipeline_data['x'], self._event_pipeline_data['y']
            )

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        )
        # self.setWindowFlags(QtCore.Qt.Tool)
        self.setWindowState(
            (self.windowState() & ~QtCore.Qt.WindowMinimized)
            | QtCore.Qt.WindowActive
        )
        # this will activate the window
        self.activateWindow()
        self.show()

    def pre_build(self):
        '''(Override)'''
        super(HarmonyQtMenuClientWidget, self).pre_build()

    def build(self):
        '''(Override)'''

        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        self._title_label = dialog.TitleLabel(label=self.windowTitle())
        self._title_label.setAlignment(QtCore.Qt.AlignCenter)
        self._title_label.setObjectName('titlebar')
        self._title_label.setMinimumHeight(24)
        title_layout.addWidget(self._title_label, 50)

        btn_close = QtWidgets.QPushButton('', parent=self)
        btn_close.setIcon(icon.MaterialIcon('close', color='#D3d4D6'))
        btn_close.setObjectName('borderless')
        btn_close.setFixedSize(24, 24)
        btn_close.clicked.connect(self.hide)
        title_layout.addWidget(btn_close)

        self.layout().addLayout(title_layout)

        for (
            widget_name,
            unused_widget_class,
            label,
            visible_in_menu,
        ) in self._widgets:
            if not visible_in_menu:
                continue

            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(partial(self._open_widget, widget_name))
            btn.setMinimumHeight(40)
            self.layout().addWidget(btn)

        self.layout().addStretch()

    def post_build(self):
        '''(Override)'''
        self._title_label.setText('  ftrack')

    def hide(self):
        self.destroy()
        self.deleteLater()

    def _open_widget(self, widget_name):
        '''Open widget with *widget_name*.'''
        self.hide()
        self._app._open_widget({'pipeline': {'name': widget_name}})
