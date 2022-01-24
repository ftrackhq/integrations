# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    definition_selector,
    line,
)
from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui import resource
from ftrack_connect_pipeline_qt.ui import theme


class QtClient(client.Client, QtWidgets.QFrame):
    '''
    Base QT client widget class.
    '''

    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE]
    # Text of the button to run the whole definition
    client_name = None

    context_changed = QtCore.Signal(object)

    def __init__(self, event_manager, parent=None):
        '''Initialise with *event_manager* and
        *parent* widget'''
        QtWidgets.QFrame.__init__(self, parent=parent)
        client.Client.__init__(self, event_manager)

        if self.get_theme():
            self.setTheme(self.get_theme())
            if self.get_background_color():
                self.setProperty('background', self.get_background_color())
        self.setObjectName(
            '{}_{}'.format(qt_constants.MAIN_FRAMEWORK_WIDGET, self.__class__.__name__)
        )

        self.is_valid_asset_name = False
        self.widget_factory = factory.WidgetFactory(
            event_manager, self.ui_types, self.client_name
        )

        self.pre_build()
        self.build()
        self.post_build()
        if self.context_id:
            self.context_selector.set_context_id(self.context_id)
        self.add_hosts(self.discover_hosts())

    def get_theme(self):
        '''Return the client theme, return None to disable themes. Can be overridden by child.'''
        return 'dark'

    def get_background_color(self):
        '''Return the theme background color style. Can be overridden by child.'''
        return 'default'

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
            self.host_and_definition_selector.set_definition_title_filter(
                self.definition_filter
            )
        if self.definition_extensions_filter:
            self.host_and_definition_selector.set_definition_extensions_filter(
                self.definition_extensions_filter
            )
        self.host_and_definition_selector.add_hosts(self.host_connections)

    def setTheme(self, selected_theme):
        theme.applyFont()
        theme.applyTheme(self, selected_theme, 'plastique')

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(5)
        self.setLayout(layout)
        # self.setAutoFillBackground(True)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)

        self.header.id_container_layout.insertWidget(
            1, self.widget_factory.progress_widget.widget
        )

        self.context_selector = ContextSelector(self.session)
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        self.layout().addWidget(line.Line())

        self.host_and_definition_selector = (
            definition_selector.DefinitionSelectorButtons(
                "Choose what to {}".format(self.client_name.lower()),
                'CLEAR' if self.client_name.lower() == 'publish' else 'REFRESH',
            )
        )
        self.host_and_definition_selector.start_over_button.clicked.connect(
            self.widget_factory.progress_widget.set_status_widget_visibility
        )
        self.layout().addWidget(self.host_and_definition_selector)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(self.scroll)

        self.run_button = QtWidgets.QPushButton(
            self.client_name.upper() if self.client_name else 'Run'
        )
        self.run_button.setObjectName('large')
        self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.context_selector.entityChanged.connect(
            self._on_context_selector_context_changed
        )
        self.host_and_definition_selector.host_changed.connect(self.change_host)
        self.host_and_definition_selector.definition_changed.connect(
            self.change_definition
        )
        self.run_button.clicked.connect(self._on_run_definition)

        self.widget_factory.widget_asset_updated.connect(self._on_widget_asset_updated)

        self.widget_factory.widget_run_plugin.connect(self._on_run_plugin)
        self.widget_factory.components_checked.connect(self._on_components_checked)
        if self.event_manager.mode == constants.LOCAL_EVENT_MODE:
            self.host_and_definition_selector.host_combobox.hide()

    def _on_context_selector_context_changed(self, context_entity):
        '''Updates the option dictionary with provided *context* when
        entityChanged of context_selector event is triggered'''
        self.context_id = context_entity['id']
        self.change_context(self.context_id)

        # keep reference of the latest selected definition
        index = self.host_and_definition_selector.get_current_definition_index()

        if len(self.host_and_definition_selector.host_connections) > 0:
            if self.event_manager.mode == constants.LOCAL_EVENT_MODE:
                self.host_and_definition_selector.change_host_index(1)
        else:
            self.host_and_definition_selector.change_host_index(0)

        if index != -1:
            self.host_and_definition_selector.set_current_definition_index(index)

    def change_context(self, context_id):
        '''
        Assign the given *context_id* as the current :obj:`context_id` and to the
        :attr:`~ftrack_connect_pipeline.client.HostConnection.context_id` emit
        on_context_change signal.
        '''
        super(QtClient, self).change_context(context_id)
        self.context_changed.emit(context_id)

    def _clear_host_widget(self):
        if self.scroll.widget():
            self.widget_factory.reset_type_widget_plugin()
            self.scroll.widget().deleteLater()

    def change_host(self, host_connection):
        '''Triggered when host_changed is called from the host_selector.'''
        self._clear_host_widget()
        super(QtClient, self).change_host(host_connection)

    def change_definition(self, schema, definition, component_names_filter):
        '''
        Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *schema* and *definition*
        '''

        if self.scroll.widget():
            self.widget_factory.reset_type_widget_plugin()
            self.scroll.widget().deleteLater()

        if not schema and not definition:
            self.definition_changed(None, 0)
            self.run_button.setText('OPEN ASSEMBLER')
            return

        super(QtClient, self).change_definition(schema, definition)

        asset_type_name = self.current_package['asset_type_name']

        self.widget_factory.set_context(self.context_id, asset_type_name)
        self.widget_factory.host_connection = self.host_connection
        self.widget_factory.set_definition_type(self.definition['type'])
        self.widget_factory.set_package(self.current_package)
        self.definition_widget = self.widget_factory.build_definition_ui(
            definition['name'], self.definition, component_names_filter
        )
        self.scroll.setWidget(self.definition_widget)
        self.run_button.setText('OPEN ASSEMBLER')

    def definition_changed(self, definition, available_components_count):
        '''Can be overridden by child'''
        pass

    def _on_widget_asset_updated(self, asset_name, asset_id, is_valid):
        self.is_valid_asset_name = is_valid

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def _on_run_definition(self):
        '''Function called when click the run button'''
        if self.definition is None:
            # TODO: Open assembler
            raise NotImplementedError('Assembler open not implemented!')
        serialized_data = self.widget_factory.to_json_object()
        if not self.is_valid_asset_name:
            msg = "Can't publish without a valid asset name"
            self.widget_factory.progress_widget.set_status(constants.ERROR_STATUS, msg)
            self.logger.error(msg)
            return
        engine_type = serialized_data['_config']['engine_type']
        self.widget_factory.progress_widget.show_widget()
        self.run_definition(serialized_data, engine_type)

    def _on_components_checked(self, available_components_count):
        self.run_button.setText(
            self.client_name.uppoer()
            if available_components_count > 0
            else 'OPEN ASSEMBLER'
        )
        self.definition_changed(self.definition, available_components_count)

    def _notify_client(self, event):
        super(QtClient, self)._notify_client(event)
        # We pass the latest log which should be the recently added one.
        # Otherwise, we have no way to check which log we should be passing
        self.widget_factory.update_widget(self.logs[-1])
