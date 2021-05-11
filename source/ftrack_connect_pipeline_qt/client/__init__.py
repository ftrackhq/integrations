# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtGui, QtCore, QtWidgets
from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline_qt.ui.utility.widget import header, definition_selector
from ftrack_connect_pipeline_qt.client.widgets import factory
from ftrack_connect_pipeline_qt import constants as qt_constants


class QtClient(client.Client, QtWidgets.QWidget):
    '''
    Base QT client widget class.
    '''

    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE]
    # Text of the button to run the whole definition
    run_definition_button_text = 'Run'

    def __init__(self, event_manager, parent=None):
        '''Initialise with *event_manager* and
        *parent* widget'''
        QtWidgets.QWidget.__init__(self, parent=parent)
        client.Client.__init__(self, event_manager)
        self.is_valid_asset_name = False
        self.widget_factory = factory.WidgetFactory(
            event_manager,
            self.ui_types
        )

        self.pre_build()
        self.build()
        self.post_build()
        self.add_hosts(self.discover_hosts())

    def add_hosts(self, host_connections):
        '''
        Adds the given *host_connections*

        *host_connections* : list of
        :class:`~ftrack_connect_pipeline.client.HostConnection`
        '''
        for host_connection in host_connections:
            if host_connection in self.host_connections:
                continue
            self._host_connections.append(host_connection)

    def _host_discovered(self, event):
        '''
        Callback, add the :class:`~ftrack_connect_pipeline.client.HostConnection`
        of the new discovered :class:`~ftrack_connect_pipeline.host.HOST` from
        the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        super(QtClient, self)._host_discovered(event)
        if self.definition_filter:
            self.host_selector.set_definition_filter(self.definition_filter)
        self.host_selector.add_hosts(self.host_connections)


    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)

        self.host_selector = definition_selector.DefinitionSelector()
        self.layout().addWidget(self.host_selector)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll)

        self.run_button = QtWidgets.QPushButton(self.run_definition_button_text)
        self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.host_changed.connect(self.change_host)
        self.host_selector.definition_changed.connect(self.change_definition)
        self.run_button.clicked.connect(self._on_run_definition)

        self.widget_factory.widget_status_updated.connect(
            self._on_widget_status_updated
        )

        self.widget_factory.widget_context_updated.connect(
            self._on_widget_context_updated
        )

        self.widget_factory.widget_asset_updated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widget_run_plugin.connect(
            self._on_run_plugin
        )

        # # apply styles
        # theme.applyTheme(self, 'dark')
        # theme.applyFont()

    def change_host(self, host_connection):
        ''' Triggered when host_changed is called from the host_selector.'''
        if self.scroll.widget():
            self.widget_factory.reset_type_widget_plugin()
            self.scroll.widget().deleteLater()
        super(QtClient, self).change_host(host_connection)

    def change_definition(self, schema, definition):
        '''
        Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *schema* and *definition*
        '''

        if self.scroll.widget():
            self.widget_factory.reset_type_widget_plugin()
            self.scroll.widget().deleteLater()

        if not schema and not definition:
            return

        super(QtClient, self).change_definition(schema, definition)

        asset_type = self.current_package['asset_type']

        context = {
            'context_id': self.context,
            'asset_type': asset_type
        }

        self.widget_factory.set_context(context)
        self.widget_factory.set_host_connection(self.host_connection)
        self.widget_factory.set_definition_type(self.definition['type'])
        self.widget_factory.set_package(self.current_package)

        self._current_def = self.widget_factory.create_widget(
            definition['name'],
            schema,
            self.definition
        )
        self.widget_factory.check_components()
        self.scroll.setWidget(self._current_def)

    def _on_widget_status_updated(self, data):
        ''' Triggered when a widget generated by the fabric has emit the
        widget_status_update signal.
        Sets the status from the given *data* to the header
        '''
        status, message = data
        self.header.setMessage(message, status)

    def _on_widget_context_updated(self, context_id):
        self.change_context(context_id)

    def _on_widget_asset_updated(self, asset_name, asset_id, is_valid):
        self.is_valid_asset_name = is_valid

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def _on_run_definition(self):
        '''Function called when click the run button'''
        serialized_data = self._current_def.to_json_object()
        if not self.is_valid_asset_name:
            msg = "Can't publish without a valid asset name"
            self.header.setMessage(msg, 'ERROR_STATUS')
            self.logger.error(msg)
            return
        engine_type = serialized_data['_config']['engine_type']
        self.run_definition(serialized_data, engine_type)


