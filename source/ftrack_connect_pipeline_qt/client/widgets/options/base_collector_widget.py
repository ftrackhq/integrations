# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial

from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

class BaseCollectorWidget(BaseOptionsWidget):
    ''' Base class to represent a Collector widget '''

    @property
    def collected_objects(self):
        '''Return the collected object by the widget'''
        return self._collected_objects

    def __init__(
        self, parent=None, session=None, data=None, name=None,
        description=None, options=None, context_id=None, asset_type_name=None
    ):
        self._collected_objects = []
        super(BaseCollectorWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context_id=context_id,
            asset_type_name=asset_type_name
        )

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(BaseCollectorWidget, self).build()
        self.add_button = QtWidgets.QPushButton("Add Selected")
        self.list_widget = QtWidgets.QListWidget()

        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )

        self.layout().addWidget(self.add_button)
        self.layout().addWidget(self.list_widget)

    def contextMenuEvent(self, event):
        '''
        Executes the context menu
        '''
        self.menu = QtWidgets.QMenu(self)
        select_action_widget = QtWidgets.QAction('Select', self)
        select_action_widget.setData('ctx_select')
        remove_action_widget = QtWidgets.QAction('Remove', self)
        remove_action_widget.setData('ctx_remove')
        self.menu.addAction(select_action_widget)
        self.menu.addAction(remove_action_widget)
        self.menu.triggered.connect(self.menu_triggered)

        # add other required actions
        self.menu.exec_(QtGui.QCursor.pos())

    def post_build(self):
        super(BaseCollectorWidget, self).post_build()
        self.list_widget.itemChanged.connect(self._on_item_changed)
        self.add_button.clicked.connect(
            partial(self.on_run_plugin, 'add')
        )
        self.set_option_result(self.collected_objects, key='collected_objects')

    def on_fetch_callback(self, result):
        '''
        Callback funtion called by the _set_internal_run_result method of the
        :class:`~ftrack_connect_pipeline_qt.client.widgets.options.BaseOptionsWidget`
        '''
        self.list_widget.clear()
        for obj in result:
            self.add_object(obj)

    def on_add_callback(self, result):
        '''
        Callback funtion called by the _set_internal_run_result method of the
        :class:`~ftrack_connect_pipeline_qt.client.widgets.options.BaseOptionsWidget`
        '''
        current_objects = self.get_current_objects()
        for obj in result:
            if obj in current_objects:
                continue
            self.add_object(obj)

    def on_select_callback(self, result):
        '''
        Callback funtion called by the _set_internal_run_result method of the
        :class:`~ftrack_connect_pipeline_qt.client.widgets.options.BaseOptionsWidget`
        '''
        self.logger.debug("selected objects: {}".format(result))

    def add_object(self, obj):
        '''Add the given *obj* to the widget list'''
        item = QtWidgets.QListWidgetItem(obj)
        self.list_widget.addItem(item)
        if item.text() not in self.collected_objects:
            self._collected_objects.append(item.text())
        if item.text() not in self._options['collected_objects']:
            self._options['collected_objects'].append(item.text())
    def get_current_objects(self):
        '''Return the objects in the :obj:`list_widget`'''
        current_objects = []
        for idx in range(0, self.list_widget.count()):
            current_objects.append(self.list_widget.item(idx).text())
        return current_objects

    def _on_item_changed(self, item):
        '''
        Callback function called when :obj:`list_widget` itemchanged signal is
        triggered
        '''
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
        selected_widget_items = self.list_widget.selectedItems()
        selected_items = []
        for item in selected_widget_items:
            selected_items.append(item.text())
        self._options['selected_items'] = selected_items
        self.on_run_plugin('select')

    def ctx_remove(self):
        '''
        Triggered when select action menu been clicked.
        '''
        selected_widget_items = self.list_widget.selectedItems()
        for item in selected_widget_items:
            self._options['collected_objects'].remove(item.text())
            self._collected_objects.remove(item.text())
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
