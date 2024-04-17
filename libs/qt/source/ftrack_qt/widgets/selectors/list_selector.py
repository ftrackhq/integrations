# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.widgets.buttons import CircularButton


class ListSelector(QtWidgets.QWidget):
    current_item_changed = QtCore.Signal(object)
    refresh_clicked = QtCore.Signal()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = str(value)

    @property
    def no_items_label(self):
        return self._no_items_label_widget.text()

    @no_items_label.setter
    def no_items_label(self, value):
        self._no_items_label_widget.set_text = str(value)

    def __init__(self, label, parent=None):
        '''
        Initialize list_selector widget

        :param parent: The parent dialog or frame
        '''
        super(ListSelector, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._label = label
        self._label_widget = None
        self._combo_box_selector = None
        self._refresh_button = None
        self._no_items_label_widget = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        # Create Label
        self._label_widget = QtWidgets.QLabel(self.label)

        # Create the no items label
        # TODO: finish this
        self._no_items_label_widget = QtWidgets.QLabel()
        self.no_items_label = '<html><i>No items available</i></html>'

        # Create the combo box
        self._combo_box_selector = QtWidgets.QComboBox()
        self._combo_box_selector.setToolTip(self.label)

        # Create the refresh button
        self._refresh_button = CircularButton('sync')

        # Set up the layout
        self.layout().addWidget(self._label_widget)
        self.layout().addWidget(self._combo_box_selector)
        self.layout().addWidget(self._refresh_button)

    def post_build(self):
        self._combo_box_selector.currentIndexChanged.connect(
            self._on_current_index_changed_callback
        )
        self._refresh_button.clicked.connect(self._on_refresh_callback)

    def clear_items(self):
        self._combo_box_selector.clear()

    def add_item(self, item_text):
        if self._combo_box_selector.count() == 0:
            # Add first empty object
            self._combo_box_selector.addItem("-- {} --".format(self.label))
        self._combo_box_selector.addItem(item_text)

    def set_current_item(self, item_text):
        if not item_text:
            self._combo_box_selector.setCurrentIndex(0)
        for index in range(0, self._combo_box_selector.count()):
            if self._combo_box_selector.itemText(index) == item_text:
                self._combo_box_selector.setCurrentIndex(index)
                break

    def set_current_item_index(self, item_index):
        self._combo_box_selector.setCurrentIndex(item_index)

    def current_item_text(self):
        return self._combo_box_selector.currentText()

    def current_item_index(self):
        return self._combo_box_selector.currentIndex()

    def _on_current_index_changed_callback(self, index):
        self.current_item_changed.emit(self._combo_box_selector.currentText())

    def _on_refresh_callback(self):
        self.refresh_clicked.emit()
