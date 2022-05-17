#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.utils import ftrack_context_id
from ftrack_connect_pipeline.client.opener import OpenerClient

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt import client

from ftrack_connect_pipeline_qt.ui.factory.opener import OpenerWidgetFactory
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    line,
    dialog,
    scroll_area,
    definition_selector,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)


class QtOpenerClient(OpenerClient, client.QtClientMixin, dialog.Dialog):
    '''
    Opener widget class.
    '''

    def __init__(
        self, event_manager, definition_extensions_filter=None, parent=None
    ):
        OpenerClient.__init__(self, event_manager)
        dialog.Dialog.__init__(self, parent=parent)

        self.logger.debug('start qt opener')

        if not definition_extensions_filter is None:
            self.definition_extensions_filter = definition_extensions_filter

        self.widget_factory = OpenerWidgetFactory(
            self.event_manager,
            self.ui_types,
            parent=self.parent(),
        )
        self.open_assembler_button = None

        client.QtClientMixin.__init__(self)  # Build widget

        self.setWindowTitle('ftrack Open')
        self.resize(450, 530)

    def getThemeBackgroundStyle(self):
        return 'ftrack'

    def is_docked(self):
        return False

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setContentsMargins(16, 16, 16, 16)
        self.layout().setSpacing(0)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session, parent=self)
        self.layout().addWidget(self.header)
        self.progress_widget = self.widget_factory.progress_widget
        self.header.content_container.layout().addWidget(
            self.progress_widget.widget
        )

        self.layout().addWidget(line.Line(style='solid', parent=self))

        self.context_selector = ContextSelector(
            self.session, enble_entity_browser=True, parent=self.parent()
        )
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        self.layout().addWidget(line.Line(parent=self))

        self.host_and_definition_selector = (
            definition_selector.OpenerDefinitionSelector(parent=self.parent())
        )
        self.host_and_definition_selector.refreshed.connect(self.refresh)

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.layout().addWidget(self.host_and_definition_selector)
        self.layout().addWidget(self.scroll, 100)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().setContentsMargins(10, 10, 10, 5)
        button_widget.layout().setSpacing(10)

        self.open_assembler_button = OpenAssemblerButton()
        button_widget.layout().addWidget(self.open_assembler_button)

        self.l_filler = QtWidgets.QLabel()
        button_widget.layout().addWidget(self.l_filler, 10)

        self.run_button = client.RunButton('OPEN')
        button_widget.layout().addWidget(self.run_button)
        self.run_button.setEnabled(False)
        self.layout().addWidget(button_widget)

    def post_build(self):
        self.context_selector.entityChanged.connect(
            self._on_context_selector_context_changed
        )
        self.host_and_definition_selector.hostChanged.connect(self.change_host)
        self.host_and_definition_selector.definitionChanged.connect(
            self.change_definition
        )

        if self.event_manager.mode == core_constants.LOCAL_EVENT_MODE:
            self.host_and_definition_selector.host_widget.hide()

        self.widget_factory.widgetRunPlugin.connect(self._on_run_plugin)
        self.widget_factory.componentsChecked.connect(
            self._on_components_checked
        )
        self.open_assembler_button.clicked.connect(self._open_assembler)
        self.run_button.clicked.connect(self.run)

    def _on_context_selector_context_changed(self, context):
        '''(Override) Context has been set in context selector'''
        if self.host_connection:
            # Send event to other listening clients
            self.host_connection.change_ftrack_context_id(context)
        super(QtOpenerClient, self)._on_context_selector_context_changed(
            context
        )

    def change_context(self, context_id):
        '''
        Assign the given *context_id* as the current :obj:`context_id` and to the
        :attr:`~ftrack_connect_pipeline.client.HostConnection.context_id` emit
        on_context_change signal.
        '''
        super(QtOpenerClient, self).change_context(context_id)
        self.context_selector.set_context_id(self.context_id)
        self.contextChanged.emit(context_id)

    def _host_discovered(self, event):
        '''
        Callback, add the :class:`~ftrack_connect_pipeline.client.HostConnection`
        of the new discovered :class:`~ftrack_connect_pipeline.host.HOST` from
        the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        super(QtOpenerClient, self)._host_discovered(event)
        if self.definition_filter:
            self.host_and_definition_selector.definition_title_filter = (
                self.definition_filter
            )
        if self.definition_extensions_filter:
            self.host_and_definition_selector.definition_extensions_filter = (
                self.definition_extensions_filter
            )
        self.host_and_definition_selector.add_hosts(self.host_connections)

    def change_host(self, host_connection):
        '''Triggered when host_changed is called from the host_selector.'''
        self._clear_widget()
        super(QtOpenerClient, self).change_host(host_connection)
        self.context_selector.host_changed(host_connection)

    def change_definition(self, schema, definition, component_names_filter):
        '''
        Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *schema* and *definition*
        '''
        self._component_names_filter = component_names_filter
        self._clear_widget()

        if not schema and not definition:
            self.definition_changed(None, 0)
            return

        super(QtOpenerClient, self).change_definition(schema, definition)

        asset_type_name = definition['asset_type']

        self.widget_factory.set_context(self.context_id, asset_type_name)
        self.widget_factory.host_connection = self.host_connection
        self.widget_factory.listen_widget_updates()
        self.widget_factory.set_definition_type(self.definition['type'])
        self.definition_widget = self.widget_factory.build_definition_ui(
            self.definition, component_names_filter
        )
        self.scroll.setWidget(self.definition_widget)

    def definition_changed(self, definition, available_components_count):
        '''React upon change of definition, or no versions/components(definitions) available.'''
        if definition is not None and available_components_count >= 1:
            self.run_button.setEnabled(True)
        else:
            self.run_button.setEnabled(False)
            self._clear_widget()

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def run(self):
        '''Function called when click the run button'''
        self.widget_factory.has_error = False
        serialized_data = self.widget_factory.to_json_object()
        engine_type = serialized_data['_config']['engine_type']
        self.widget_factory.progress_widget.show_widget()
        self.run_definition(serialized_data, engine_type)
        if not self.widget_factory.has_error:
            self.widget_factory.progress_widget.set_status(
                core_constants.SUCCESS_STATUS, 'Successfully opened version!'
            )

    def _on_log_item_added(self, log_item):
        self.widget_factory.update_widget(log_item)

    def refresh(self):
        '''Called upon definition selector refresh button click.'''
        self.widget_factory.progress_widget.set_status_widget_visibility(False)

    def _launch_context_selector(self):
        '''Close client (if not docked) and open entity browser.'''
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_widget(core_constants.CHANGE_CONTEXT)


class OpenAssemblerButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(OpenAssemblerButton, self).__init__(
            'OPEN ASSEMBLER', parent=parent
        )
        self.setMinimumWidth(128)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)
