# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import uuid

from PySide import QtGui

import ftrack_connect.ui.widget.components_list
import ftrack_connect.ui.widget.item_selector
from harness import Harness


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        widget.setLayout(layout)

        # Create components selector
        selector = ftrack_connect.ui.widget.item_selector.ItemSelector(
            labelField='componentName',
            defaultLabel='Unnamed component',
            emptyLabel='Select component to use as preview',
        )

        # Create components list
        componentsList = (
            ftrack_connect.ui.widget.components_list.ComponentsList()
        )

        # Create a button to add new components
        def _addComponent():
            fileName = str(uuid.uuid4())[:6]
            componentsList.addItem(
                {'resourceIdentifier': '/path/to/{}.ext'.format(fileName)}
            )

        addComponentButton = QtGui.QPushButton('Add component')
        addComponentButton.clicked.connect(_addComponent)

        # Connect itemsChanged to update selector when list changes.
        def _onItemsChanged():
            selector.setItems(componentsList.items())

        componentsList.itemsChanged.connect(_onItemsChanged)

        # Add widgets and show dialog.
        layout.addWidget(addComponentButton)
        layout.addWidget(componentsList)
        layout.addWidget(selector)

        return widget


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
