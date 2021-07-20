# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtGui, QtCore, QtWidgets
from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline_qt.ui.utility.widget import header, definition_selector
from ftrack_connect_pipeline_qt.client.widgets import factory
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import ContextSelector


class QtClient(client.Client, QtWidgets.QWidget):
    '''
    Base QT client widget class.
    '''

    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE]
    # Text of the button to run the whole definition
    run_definition_button_text = 'Run'

    on_context_change = QtCore.Signal(object)

    @property
    def context_entity(self):
        '''Returns the context_entity'''
        return self._context_entity

    @context_entity.setter
    def context_entity(self, value):
        '''Sets context_entity with the given *value*'''
        self._context_entity = value

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
        if self.context_id:
            context_entity = self.session.query(
                'select link, name , parent, parent.name from Context where id is "{}"'.format(self.context_id)
            ).one()
            self.context_selector.setEntity(context_entity)
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

        self.context_selector = ContextSelector(self.session)

        self.layout().addWidget(self.context_selector)

        self.host_selector = definition_selector.DefinitionSelector()
        self.layout().addWidget(self.host_selector)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll)

        self.run_button = QtWidgets.QPushButton(self.run_definition_button_text)
        self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.context_selector.entityChanged.connect(self._on_context_selector_context_changed)
        self.host_selector.host_changed.connect(self.change_host)
        self.host_selector.definition_changed.connect(self.change_definition)
        self.run_button.clicked.connect(self._on_run_definition)

        self.widget_factory.widget_status_updated.connect(
            self._on_widget_status_updated
        )

        self.widget_factory.widget_asset_updated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widget_run_plugin.connect(
            self._on_run_plugin
        )
        if self.event_manager.mode == constants.LOCAL_EVENT_MODE:
            self.host_selector.host_combobox.hide()

        # # apply styles
        # theme.applyTheme(self, 'dark')
        # theme.applyFont()

    def _on_context_selector_context_changed(self, context_entity):
        '''Updates the option dicctionary with provided *context* when
        entityChanged of context_selector event is triggered'''
        self.context_entity = context_entity
        self.change_context(context_entity['id'])
        if self.event_manager.mode == constants.LOCAL_EVENT_MODE:
            self.host_selector.change_host_index(1)

    def change_context(self, context_id):
        '''
        Assign the given *context_id* as the current :obj:`context_id` and to the
        :attr:`~ftrack_connect_pipeline.client.HostConnection.context_id` emit
        on_context_change signal.
        '''
        super(QtClient, self).change_context(context_id)
        self.on_context_change.emit(context_id)

    def _clear_host_widget(self):
        if self.scroll.widget():
            self.widget_factory.reset_type_widget_plugin()
            self.scroll.widget().deleteLater()

    def change_host(self, host_connection):
        ''' Triggered when host_changed is called from the host_selector.'''
        self._clear_host_widget()
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

        asset_type_name = self.current_package['asset_type_name']

        self.widget_factory.set_context(self.context_id, asset_type_name)
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


