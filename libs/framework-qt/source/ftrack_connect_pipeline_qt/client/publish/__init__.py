#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import ftrack_connect_pipeline_qt.ui.utility.widget.button
from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client import constants as client_constants
from ftrack_connect_pipeline.client.publisher import PublisherClient

from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.factory.publisher import (
    PublisherWidgetFactory,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    header,
    line,
    host_selector,
    definition_selector,
    scroll_area,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)


class QtPublisherClient(PublisherClient):
    '''
    Client for publishing DCC asset data to ftrack and storage, through location system
    '''

    ui_types = [core_constants.UI_TYPE, qt_constants.UI_TYPE]

    def __init__(self, event_manager):
        super(QtPublisherClient, self).__init__(event_manager)
        self.logger.debug('start qt publisher')


class QtPublisherClientWidget(QtPublisherClient, QtWidgets.QFrame):
    '''
    Publisher client widget class.
    '''

    contextChanged = QtCore.Signal(object)  # Context has changed

    def __init__(self, event_manager, parent=None):
        QtWidgets.QFrame.__init__(self, parent=parent)
        QtPublisherClient.__init__(self, event_manager)

        self.logger.debug('start qt publisher widget')

        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        self.setProperty('docked', 'true' if self.is_docked() else 'false')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # Check if a proper storage scenario is setup or not
        location_message = None
        test_location = self.session.pick_location()
        if test_location is None:
            location_message = 'No ftrack location were discoverable, publishing not possible!'
            dialog.ModalDialog(parent, message=location_message)
            raise Exception(location_message)
        elif test_location['name'] == 'ftrack.unmanaged':
            location_message = 'No ftrack storage scenario have been setup!'
            if not dialog.ModalDialog(
                parent,
                title='ftrack Publisher',
                question='{} Continue anyway and have published files stay in your temp folder?'.format(
                    location_message
                ),
            ).exec_():
                raise Exception(location_message)
        if location_message:
            self.logger.warning(location_message)

        self.widget_factory = PublisherWidgetFactory(
            self.event_manager, self.ui_types
        )
        self.is_valid_asset_name = False
        self.open_assembler_button = None
        self.scroll = None  # Main content scroll pane

        self.pre_build()
        self.build()
        self.post_build()

        self.discover_hosts()

        self.setWindowTitle('Standalone Pipeline Publisher')

    def get_theme_background_style(self):
        '''Return the theme background color style. Can be overridden by child.'''
        return 'default'

    def is_docked(self):
        return True

    # Build

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setContentsMargins(0, 0, 0, 5)
        self.layout().setSpacing(0)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)
        self.progress_widget = self.widget_factory.progress_widget
        self.header.content_container.layout().addWidget(
            self.progress_widget.widget
        )

        self.host_selector = host_selector.HostSelector(self)
        self.layout().addWidget(self.host_selector)

        self.layout().addWidget(line.Line(style='solid'))

        self.context_selector = ContextSelector(self.session)
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        self.layout().addWidget(line.Line())

        self.definition_selector = (
            definition_selector.PublisherDefinitionSelector()
        )
        self.definition_selector.refreshed.connect(self.refresh)

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.layout().addWidget(self.definition_selector)
        self.layout().addWidget(self.scroll, 100)

        self.layout().addWidget(self._build_button_widget())
        self.run_button.setText('PUBLISH')

    def _build_button_widget(self):
        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().setContentsMargins(10, 10, 10, 5)
        button_widget.layout().setSpacing(10)

        self.run_button = (
            ftrack_connect_pipeline_qt.ui.utility.widget.button.RunButton(
                'PUBLISH'
            )
        )
        button_widget.layout().addWidget(self.run_button)
        self.run_button.setEnabled(False)
        return button_widget

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.hostChanged.connect(self.change_host)
        self.contextChanged.connect(self.on_context_changed_sync)
        self.definition_selector.definitionChanged.connect(
            self.change_definition
        )

        self.run_button.clicked.connect(self.run)
        self.context_selector.changeContextClicked.connect(
            self._launch_context_selector
        )
        self.widget_factory.widgetAssetUpdated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widgetRunPlugin.connect(self._on_run_plugin)
        self.widget_factory.componentsChecked.connect(
            self._on_components_checked
        )
        self.setMinimumWidth(300)

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        self.host_selector.add_hosts(host_connections)

    def on_host_changed(self, host_connection):
        '''Triggered when client has set host connection'''
        self._clear_widget()
        if self.definition_filters:
            self.definition_selector.definition_filters = (
                self.definition_filters
            )
        if self.definition_extensions_filter:
            self.definition_selector.definition_extensions_filter = (
                self.definition_extensions_filter
            )
        self.definition_selector.on_host_changed(host_connection)

    # Context

    def on_context_changed(self, context_id):
        '''Async call upon context changed'''
        self.contextChanged.emit(context_id)

    def on_context_changed_sync(self, context_id):
        '''Context has been set'''
        self.context_selector.context_id = context_id

        # Reset definition selector and clear client
        self.definition_selector.clear_definitions()
        self._clear_widget()
        self.definition_selector.populate_definitions()

        # If only one publisher, select it
        if len(self.definition_selector.definitions) == 1:
            self.definition_selector.current_definition_index = 1

    # Definition

    def change_definition(self, definition, schema, component_names_filter):
        '''
        Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *schema* and *definition*
        '''
        self._component_names_filter = component_names_filter
        self._clear_widget()

        if not schema and not definition:
            self.definition_changed(None, 0)
            return

        super(QtPublisherClientWidget, self).change_definition(
            definition, schema
        )

        asset_type_name = definition['asset_type']

        self.widget_factory.set_context(self.context_id, asset_type_name)
        self.widget_factory.host_connection = self.host_connection
        self.widget_factory.set_definition_type(self.definition['type'])
        self.definition_widget = self.widget_factory.build(
            self.definition, component_names_filter, None
        )
        self.scroll.setWidget(self.definition_widget)

    def definition_changed(self, definition, available_components_count):
        '''Can be overridden by child'''
        pass

    # User

    def _clear_widget(self):
        '''Remove main client widget'''
        if self.scroll and self.scroll.widget():
            self.scroll.widget().deleteLater()

    def _on_widget_asset_updated(self, asset_name, asset_id, is_valid):
        if asset_id is None:
            self.is_valid_asset_name = is_valid
        else:
            self.is_valid_asset_name = True

    def _on_components_checked(self, available_components_count):
        self.definition_changed(self.definition, available_components_count)
        self.run_button.setEnabled(available_components_count >= 1)
        if available_components_count == 0:
            self._clear_widget()

    # Run

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def _on_log_item_added(self, log_item):
        self.widget_factory.update_widget(log_item)

    def run(self):
        '''Function called when click the run button'''
        self.widget_factory.has_error = False
        serialized_data = self.widget_factory.to_json_object()
        if not self.is_valid_asset_name:
            msg = "Can't publish without a valid asset name"
            self.widget_factory.progress_widget.set_status(
                core_constants.ERROR_STATUS, msg
            )
            self.logger.error(msg)
            return False
        engine_type = serialized_data['_config']['engine_type']
        self.widget_factory.listen_widget_updates()
        try:
            self.widget_factory.progress_widget.show_widget()
            self.widget_factory.progress_widget.reset_statuses()
            self.run_definition(serialized_data, engine_type)
            if not self.widget_factory.has_error:
                self.widget_factory.progress_widget.set_status(
                    core_constants.SUCCESS_STATUS,
                    'Successfully published {}!'.format(
                        self.definition['name'][
                            : self.definition['name'].rfind(' ')
                        ].lower()
                    ),
                )
        finally:
            self.widget_factory.end_widget_updates()

    def refresh(self):
        '''Called upon definition selector refresh button click.'''
        self.widget_factory.progress_widget.set_status_widget_visibility(False)

    def _launch_context_selector(self):
        '''Close client (if not docked) and open entity browser.'''
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_client(qt_constants.CHANGE_CONTEXT_WIDGET)

    def closeEvent(self, e):
        super(QtPublisherClientWidget, self).closeEvent(e)
        self.logger.debug('closing qt client')
        # Unsubscribe to context change events
        self.unsubscribe_host_context_change()
