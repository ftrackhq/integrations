# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.overlay import OverlayWidget
from ftrack_qt.widgets.lines import LineWidget
from ftrack_qt.utils.widget import (
    get_main_window_from_widget,
    get_framework_main_dialog,
)


class OptionsButton(QtWidgets.QPushButton):
    '''Options button on publisher accordion'''

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
        self._overlay_container = OverlayWidget(
            self._main_widget, height_percentage=0.9
        )
        self._overlay_container.setVisible(False)

    def post_build(self):
        self.clicked.connect(self.on_click_callback)

    def on_click_callback(self):
        '''Callback on clicking the options button, show the publish options overlay'''
        # Check first if widget is running on a ftrack framework dialog
        main_window = get_framework_main_dialog(self)
        if not main_window:
            main_window = get_main_window_from_widget(self)
        if main_window:
            self._overlay_container.setParent(main_window)
        self._overlay_container.setVisible(True)

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
