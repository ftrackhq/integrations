# :coding: utf-8
# :copyright: Copyright (c) 2015-2023 ftrack

import logging

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.buttons import CircularButton


class ListSelector(QtWidgets.QWidget):

    @property
    def label(self):
        return self._label_widget.text()

    @label.setter
    def label(self, value):
        self._label_widget.set_text = str(value)

    @property
    def no_items_label(self):
        return self._label_widget.text()

    @no_items_label.setter
    def no_items_label(self, value):
        self._label_widget.set_text = str(value)

    @property
    def items(self):
        return self._combo_box_selector.items()

    @items.setter
    def items(self, items):
        self._combo_box_selector.addItems(items)

    def __init__(self, parent=None):
        '''
        Initialize DefinitionSelector widget

        :param parent: The parent dialog or frame
        '''
        super(ListSelector, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._label_widget = None
        self._combo_box_selector = None
        self._refresh_button = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        # Create Label
        self._label_widget = QtWidgets.QLabel()

        # Create the no items label
        # TODO: finish this
        self._no_items_label = QtWidgets.QLabel()

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
        self._combo_box_selector.currentIndex_changed.connect(
            self._on_current_index_changed_callback
        )
        self._refresh_button.clicked.connect(self._on_refresh_callback)

    def clear_items(self):
        self._combo_box_selector.clear()

    def add_item(self, item):
        self._combo_box_selector.addItem(item)

    def _on_current_index_changed_callback(self):
        pass

    def _on_refresh_callback(self):
        pass
