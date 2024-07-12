# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class MenuButton(QtWidgets.QWidget):
    item_clicked = QtCore.Signal(object)

    @property
    def button_widget(self):
        return self._button_widget

    @property
    def menu_items(self):
        return self._menu_items

    def __init__(self, button_widget, menu_items=None, parent=None):
        super(MenuButton, self).__init__(parent)

        self._button_widget = button_widget
        if not menu_items:
            menu_items = []
        self._menu_items = menu_items

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self.button_widget)

    def post_build(self):
        self.button_widget.clicked.connect(self.show_menu)

    def add_item(self, item_data, label):
        self.menu_items.append(
            {
                'data': item_data,
                'label': label,
            }
        )

    def show_menu(self):
        if len(self.menu_items) == 1:
            return self.menu_item_selected(self.menu_items[0])
        # Create a QMenu
        menu = QtWidgets.QMenu(self.button_widget)

        # Add menu items
        for _item in self.menu_items:
            action = menu.addAction(_item['label'])
            # Connect each action to a slot (optional)
            action.triggered.connect(partial(self.menu_item_selected, _item))

        # Show the menu below the button
        menu.exec_(
            self.button_widget.mapToGlobal(
                QtCore.QPoint(0, self.button_widget.height())
            )
        )

    def menu_item_selected(self, item):
        # Handle the selected menu item (this is a placeholder for your custom logic)
        self.item_clicked.emit(item['data'])
