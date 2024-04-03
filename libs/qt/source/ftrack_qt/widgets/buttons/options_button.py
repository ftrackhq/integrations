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
        self._scroll = None
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
        self._options_widget = QtWidgets.QFrame()
        self._options_widget.setObjectName('overlay')
        self._options_widget.setLayout(QtWidgets.QVBoxLayout())

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
            self._options_widget.layout().addWidget(LineWidget())
            section_label = QtWidgets.QLabel("{}:".format(section_name))
            section_label.setObjectName('gray')
            self._options_widget.layout().addWidget(
                section_label,
            )
            section_widget = QtWidgets.QWidget()
            section_widget_layout = QtWidgets.QVBoxLayout()
            section_widget.setLayout(section_widget_layout)
            self._options_widget.layout().addWidget(section_widget)

            self.__section_registry[section_name] = section_widget

        self.__section_registry[section_name].layout().addWidget(LineWidget())
        self.__section_registry[section_name].layout().addWidget(widget)

    def finalize_options_widget(self):
        '''Finalize the options widget after it has been built, create overlay'''

        self._options_widget.layout().addWidget(QtWidgets.QLabel(''), 100)

        self._main_widget = QtWidgets.QFrame()
        self._main_widget.setLayout(QtWidgets.QVBoxLayout())
        self._main_widget.layout().setAlignment(
            QtCore.Qt.AlignmentFlag.AlignTop
        )

        title_label = QtWidgets.QLabel(self._title)
        title_label.setObjectName('h2')
        self._main_widget.layout().addWidget(title_label)
        self._main_widget.layout().addWidget(QtWidgets.QLabel(''))

        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidget(self._options_widget)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._main_widget.layout().addWidget(self._scroll, 100)

        self._overlay_container = OverlayWidget(self._main_widget)
        self._overlay_container.setVisible(False)
