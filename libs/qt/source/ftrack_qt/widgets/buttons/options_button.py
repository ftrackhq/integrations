# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.widgets.overlay import OverlayWidget
from ftrack_qt.widgets.lines import LineWidget
from ftrack_qt.utils.widget import (
    get_main_window_from_widget,
    get_framework_main_dialog,
)


class OptionsButton(QtWidgets.QPushButton):
    '''Options button on publisher accordion'''

    show_overlay_signal = QtCore.Signal(object)
    hide_overlay_signal = QtCore.Signal()

    def __init__(self, title, icon, parent=None):
        '''
        Initialize options button

        :param title: The name of the step (component)
        :param icon: The button icon to use
        :param parent: the parent dialog or frame
        '''
        super(OptionsButton, self).__init__(parent=parent)
        self._title = title
        self._icon = icon
        self.__section_registry = {}

        self._main_widget = None
        self._options_widget = None
        self._overlay_container = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumSize(30, 30)
        self.setMaximumSize(30, 30)
        self.setIcon(self._icon)
        self.setFlat(True)

    def build(self):
        self._main_widget = QtWidgets.QFrame()
        self._main_widget.setLayout(QtWidgets.QVBoxLayout())
        self._main_widget.layout().setAlignment(QtCore.Qt.AlignTop)

        title_label = QtWidgets.QLabel(self._title)
        title_label.setProperty('h2', True)
        self._main_widget.layout().addWidget(title_label)
        self._main_widget.layout().addWidget(QtWidgets.QLabel(''))
        self._main_widget.layout().setContentsMargins(0, 0, 0, 0)

        self._options_widget = QtWidgets.QWidget()
        self._options_widget.setLayout(QtWidgets.QVBoxLayout())
        self._options_widget.layout().addWidget(
            QtWidgets.QLabel(''), 100
        )  # spacer

        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(self._options_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self._main_widget.layout().addWidget(scroll)

        self._overlay_widget = OverlayWidget()

        self._overlay_widget.set_widget(self._main_widget)

    def post_build(self):
        self.clicked.connect(self.on_click_callback)
        self._overlay_widget.close_button_clicked.connect(
            self._on_overlay_close_callback
        )

    def on_click_callback(self):
        '''Callback on clicking the options button, show the publish options overlay'''
        self.show_overlay_signal.emit(self._overlay_widget)

    def _on_overlay_close_callback(self):
        '''Emits a hide_overlay_signal when overlay close button is clicked'''
        self.hide_overlay_signal.emit()

    def add_widget(self, widget, section_name):
        if section_name not in self.__section_registry:
            self._options_widget.layout().insertWidget(
                self._options_widget.layout().count() - 1, LineWidget()
            )
            section_label = QtWidgets.QLabel("{}:".format(section_name))
            section_label.setProperty('secondary', True)
            self._options_widget.layout().insertWidget(
                self._options_widget.layout().count() - 1,
                section_label,
            )
            section_widget = QtWidgets.QWidget()
            section_widget_layout = QtWidgets.QVBoxLayout()
            section_widget.setLayout(section_widget_layout)
            self._options_widget.layout().insertWidget(
                self._options_widget.layout().count() - 1, section_widget
            )

            # TODO: create the section Widget
            self.__section_registry[section_name] = section_widget

        self.__section_registry[section_name].layout().insertWidget(
            self._options_widget.layout().count() - 1, LineWidget()
        )
        self.__section_registry[section_name].layout().insertWidget(
            self._options_widget.layout().count() - 1, widget
        )

    def teardown(self):
        '''Delete the overlay widget and main widget'''
        self._main_widget.deleteLater()
        self._overlay_widget.deleteLater()
