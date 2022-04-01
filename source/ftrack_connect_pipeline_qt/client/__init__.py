# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import platform
import logging
import subprocess

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline.utils import str_context
from ftrack_connect_pipeline.client import Client, constants
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    definition_selector,
    line,
    dialog,
)
from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui import (
    resource,
)  # Important to keep this in order to bootstrap resources
from ftrack_connect_pipeline_qt.ui import theme
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)


class QtClient(Client, QtWidgets.QFrame):
    '''
    Base QT client widget class.
    '''

    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE]

    # Text of the button to run the whole definition
    client_name = None

    # Have assembler match on file extension (relaxed)
    assembler_match_extension = False

    contextChanged = QtCore.Signal(object)  # Client context has changed

    _shown = False

    def __init__(self, event_manager, parent_window, parent=None):
        '''Initialise with *event_manager* and
        *parent* widget'''
        QtWidgets.QFrame.__init__(self, parent=parent)
        Client.__init__(self, event_manager)

        self._parent_window = parent_window
        self.is_valid_asset_name = False
        self._shown = False
        self._postponed_change_definition = None

        if self.getTheme():
            self.setTheme(self.getTheme())
            if self.getThemeBackgroundStyle():
                self.setProperty('background', self.getThemeBackgroundStyle())
        self.setProperty('docked', 'true' if self.is_docked() else 'false')
        self.setObjectName(
            '{}_{}'.format(
                qt_constants.MAIN_FRAMEWORK_WIDGET, self.__class__.__name__
            )
        )

        self.scroll = None

        self.pre_build()
        self.build()
        self.post_build()

        if self.context_id:
            self.context_selector.set_context_id(self.context_id)
        self.add_hosts(self.discover_hosts())

    def getTheme(self):
        '''Return the client theme, return None to disable themes. Can be overridden by child.'''
        return 'dark'

    def setTheme(self, selected_theme):
        theme.applyFont()
        theme.applyTheme(self, selected_theme, 'plastique')

    def getThemeBackgroundStyle(self):
        '''Return the theme background color style. Can be overridden by child.'''
        return 'default'

    def get_parent_window(self):
        '''Return the dialog or DCC app window this client is within.'''
        return self._parent_window

    def is_docked(self):
        raise NotImplementedError()

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

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        if self.is_docked():
            self.layout().setContentsMargins(0, 0, 0, 5)
        else:
            self.layout().setContentsMargins(16, 16, 16, 16)
        self.layout().setSpacing(0)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(
            self.session,
            title='CONNECT',
        )
        self.layout().addWidget(self.header)

        self.progress_widget = self.widget_factory.progress_widget

        self.header.content_container.layout().addWidget(
            self.progress_widget.widget
        )

        self.context_selector = ContextSelector(self, self.session)
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        self.layout().addWidget(line.Line())

        self.host_and_definition_selector = (
            definition_selector.DefinitionSelectorWidgetComboBox(
                self.client_name
            )
        )
        self.host_and_definition_selector.refreshed.connect(self.refresh)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.layout().addWidget(self.host_and_definition_selector)
        self.layout().addWidget(self.scroll, 100)

        self.run_button = RunButton(
            self.client_name.upper() if self.client_name else 'Run'
        )
        self.layout().addWidget(self.run_button)
        self.run_button.setVisible(False)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.context_selector.entityChanged.connect(
            self._on_context_selector_context_changed
        )
        self.host_and_definition_selector.host_changed.connect(
            self.change_host
        )
        self.host_and_definition_selector.definition_changed.connect(
            self.change_definition
        )

        if self.event_manager.mode == constants.LOCAL_EVENT_MODE:
            self.host_and_definition_selector.host_combobox.hide()

        self.run_button.clicked.connect(self.run)

    def _on_context_selector_context_changed(
        self, context_entity, global_context_change
    ):
        '''Updates the option dictionary with provided *context* when
        entityChanged of context_selector event is triggered'''

        self.context_id = context_entity['id']
        self.change_context(self.context_id)

        if global_context_change:
            # Reset definitions
            self.host_and_definition_selector.clear_definitions()
            self.host_and_definition_selector.populate_definitions()
            self._clear_widget()

    def change_context(self, context_id):
        '''
        Assign the given *context_id* as the current :obj:`context_id` and to the
        :attr:`~ftrack_connect_pipeline.client.HostConnection.context_id` emit
        on_context_change signal.
        '''
        super(QtClient, self).change_context(context_id)
        self.contextChanged.emit(context_id)

    def _clear_widget(self):
        if self.scroll and self.scroll.widget():
            self.scroll.widget().deleteLater()

    def change_host(self, host_connection):
        '''Triggered when host_changed is called from the host_selector.'''
        self._clear_widget()
        super(QtClient, self).change_host(host_connection)
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

        super(QtClient, self).change_definition(schema, definition)

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
        '''Can be overridden by child'''
        pass

    def _on_widget_asset_updated(self, asset_name, asset_id, is_valid):
        if asset_id is None:
            self.is_valid_asset_name = is_valid
        else:
            self.is_valid_asset_name = True

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def run(self):
        '''Function called when click the run button'''
        self.widget_factory.has_error = False
        serialized_data = self.widget_factory.to_json_object()
        if not self.is_valid_asset_name:
            msg = "Can't publish without a valid asset name"
            self.widget_factory.progress_widget.set_status(
                constants.ERROR_STATUS, msg
            )
            self.logger.error(msg)
            return False
        engine_type = serialized_data['_config']['engine_type']
        self.widget_factory.progress_widget.show_widget()
        self.run_definition(serialized_data, engine_type, False)
        return not self.widget_factory.has_error

    def _on_components_checked(self, available_components_count):
        self.definition_changed(self.definition, available_components_count)

    def _on_log_item_added(self, log_item):
        if self.widget_factory:
            self.widget_factory.update_widget(log_item)

    def refresh(self):
        '''Called upon definition selector refresh button click.'''
        if self.widget_factory:
            self.widget_factory.progress_widget.set_status_widget_visibility(
                False
            )

    def conditional_rebuild(self):
        if self._shown:
            # Refresh when re-opened
            self.host_and_definition_selector.refresh()
        self._shown = True

    def showEvent(self, event):
        if self._postponed_change_definition:
            (
                schema,
                definition,
                component_names_filter,
            ) = self._postponed_change_definition
            self.change_definition(schema, definition, component_names_filter)
        self._shown = True
        event.accept()


class QtChangeContextClient(Client):
    '''Client for changing the current working context.'''

    def __init__(self, event_manager, unused_asset_list_model):
        Client.__init__(self, event_manager)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._host_connection = None

        self.pre_build()
        self.post_build()

    def pre_build(self):
        self.entity_browser = EntityBrowser(
            None,
            self.session,
            title='CHOOSE TASK (WORKING CONTEXT)',
        )

    def post_build(self):
        self._host_connections = self.discover_hosts()
        if len(self._host_connections) == 1:
            self._host_connection = self._host_connections[0]

    def show(self):
        # Find my host
        if self._host_connection is None:
            if len(self._host_connections) == 0:
                dialog.ModalDialog(
                    None,
                    title='Change context',
                    message='No host detected, cannot change context!',
                )
                return
            # Need to choose host connection
            self._host_connections[0].launch_widget(qt_constants.OPEN_WIDGET)
            return
        self.entity_browser.setMinimumWidth(600)
        if self.entity_browser.exec_():
            self.set_entity(self.entity_browser.entity)
            dialog.ModalDialog(
                None,
                title='Change context',
                message="Working context is now: {}".format(
                    str_context(self.entity_browser.entity)
                ),
            )

    def set_entity(self, context):
        self._host_connection.set_context(context)


class QtDocumentationClient:
    '''Client for opening Connect documentation'''

    def __init__(self, unused_event_manager, unused_asset_list_model):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def show(self):
        DOC_URL = 'https://www.ftrack.com/en/portfolio/connect'
        if platform.system() == "Windows":
            commands = ['start']
        elif platform.system() == "Darwin":
            commands = ['open']
        else:
            # Assume linux
            commands = ['xdg-open']
        commands.append(DOC_URL)
        self.logger.debug(
            'Launching documentation through system command: {}'.format(
                commands
            )
        )
        subprocess.Popen(commands)


class RunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(RunButton, self).__init__(label, parent=parent)
