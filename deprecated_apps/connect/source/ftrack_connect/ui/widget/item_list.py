# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import ftrack_connect.ui.widget.list


class ItemList(QtWidgets.QFrame):
    '''Manage a list of items represented by widgets.'''

    itemsChanged = QtCore.Signal()

    def __init__(self, widgetFactory, widgetItem, parent=None):
        '''Initialise widget with *parent*.

        *widgetFactory* should be a callable that accepts an item and returns
        an appropriate widget.

        *widgetItem* should be a callable that accepts a widget and returns
        the appropriate item from the widget.

        '''
        self.widgetFactory = widgetFactory
        self.widgetItem = widgetItem

        super(ItemList, self).__init__(parent=parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.setFrameStyle(
            QtWidgets.QFrame.Shape.StyledPanel | QtWidgets.QFrame.Shape.NoFrame
        )

        # List
        self.list = ftrack_connect.ui.widget.list.List()
        self.layout().addWidget(self.list, stretch=1)

        self.layout().setContentsMargins(5, 5, 5, 5)

    def count(self):
        '''Return count of items in list.'''
        return self.list.count()

    def addItem(self, item, row=None):
        '''Add *item* at *row*.

        If *row* not specified then add to end of list.

        Return row item added at.

        '''
        widget = self.widgetFactory(item)
        row = self.list.addWidget(widget, row)
        self.itemsChanged.emit()

        return row

    def removeItem(self, row):
        '''Remove item at *row*.'''
        self.list.removeWidget(row)
        self.itemsChanged.emit()

    def clearItems(self):
        '''Remove all items.'''
        self.list.clearWidgets()
        self.itemsChanged.emit()

    def indexOfItem(self, item):
        '''Return row of *item* in list or None if not present.'''
        index = None

        for row in range(self.count()):
            widget = self.list.widgetAt(row)
            if self.widgetItem(widget) == item:
                index = row
                break

        return index

    def items(self):
        '''Return list of items.'''
        items = []
        for row in range(self.count()):
            widget = self.list.widgetAt(row)
            items.append(self.widgetItem(widget))

        return items

    def itemAt(self, row):
        '''Return item at *row*.'''
        widget = self.list.widgetAt(row)
        return self.widgetItem(widget)
