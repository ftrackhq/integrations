# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os
from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

class BaseCollectorWidget(BaseOptionsWidget):

    @property
    def collected_objects(self):
        return self._collected_objects

    def __init__(
        self, parent=None, session=None, data=None, name=None,
        description=None, options=None, context=None
    ):
        # Collect objects
        self._collected_objects = []
        self.collect_objects()

        super(BaseCollectorWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context=context
        )

    def collect_objects(self):
        raise NotImplementedError()

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(BaseCollectorWidget, self).build()
        self.add_button = QtWidgets.QPushButton("add Object")
        self.list_widget = QtWidgets.QListWidget()

        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )

        for row, obj in enumerate(self.collected_objects):
            item = QtWidgets.QListWidgetItem(obj)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            self.list_widget.addItem(item)

        self.layout().addWidget(self.add_button)
        self.layout().addWidget(self.list_widget)

    def contextMenuEvent(self, event):
        '''
        Executes the context menu
        '''
        self.menu = QtWidgets.QMenu(self)
        action_widget = QtWidgets.QAction('Select', self)
        action_widget.setData('ctx_select')
        self.menu.addAction(action_widget)
        self.menu.triggered.connect(self.menu_triggered)

        # add other required actions
        self.menu.exec_(QtGui.QCursor.pos())

    def post_build(self):
        super(BaseCollectorWidget, self).post_build()
        self.add_button.clicked.connect(self._on_add_objects)
        self.list_widget.itemChanged.connect(self._on_item_changed)

        self.set_option_result(self.collected_objects, key='collected_objects')

    def _on_add_objects(self):
        raise NotImplementedError()

    def add_object(self, obj):
        item = QtWidgets.QListWidgetItem(obj)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked)
        self.list_widget.addItem(item)
        self._options['collected_objects'].append(item.text())

    def get_current_objects(self):
        current_objects = []
        for idx in range(0, self.list_widget.count()):
            current_objects.append(self.list_widget.item(idx).text())
        return current_objects

    def _on_item_changed(self, item):
        if not item.checkState():
            self._options['collected_objects'].remove(item.text())
        else:
            if item.text() not in self._options['collected_objects']:
                self._options['collected_objects'].append(item.text())

    def menu_triggered(self, action):
        '''
        Find and call the clicked function on the menu
        '''
        ui_callback = action.data()
        if hasattr(self, ui_callback):
            callback_fn = getattr(self, ui_callback)
            callback_fn()

    def ctx_select(self):
        '''
        Triggered when select action menu been clicked.
        '''
        selected_items = self.list_widget.selectedItems()
        return selected_items