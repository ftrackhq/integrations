# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import platform
import logging
import subprocess

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client import Client, constants
from ftrack_connect_pipeline.utils import ftrack_context_id
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    line,
    dialog,
    scroll_area,
)
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)

# DO NOT REMOVE UNUSED IMPORT - important to keep this in order to have resources
# initialised properly for applying style and providing images & fonts.
from ftrack_connect_pipeline_qt.ui import (
    resource,
)
from ftrack_connect_pipeline_qt.ui import theme
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)

#
# class QtClient():
#     '''
#     Base QT client widget class.
#     '''
#
#     ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE]
#
#     contextChanged = QtCore.Signal(object)  # Client context has changed
#
#     _shown = False
#
#     def __init__(self, event_manager):
#         '''Initialise with *event_manager* and
#         *parent* widget'''
#         super(QtClient, self).__init__(event_manager)
#
#         self.widget_factory = self.get_factory()
#         self.is_valid_asset_name = False
#         self._shown = False
#         self.open_assembler_button = None
#
#         if self.getTheme():
#             self.setTheme(self.getTheme())
#             if self.getThemeBackgroundStyle():
#                 self.setProperty('background', self.getThemeBackgroundStyle())
#         self.setProperty('docked', 'true' if self.is_docked() else 'false')
#         self.setObjectName(
#             '{}_{}'.format(
#                 qt_constants.MAIN_FRAMEWORK_WIDGET, self.__class__.__name__
#             )
#         )
#
#         self.scroll = None
#
#         self.pre_build()
#         self.build()
#         self.post_build()
#
#         self.set_context_id(self.context_id or ftrack_context_id())
#         if self.context_id:
#             self.add_hosts(self.discover_hosts())
#
#     def get_factory(self):
#         '''Instantiate the widget factory to use'''
#         raise NotImplementedError()
#
#     def getTheme(self):
#         '''Return the client theme, return None to disable themes. Can be overridden by child.'''
#         return 'dark'
#
#     def setTheme(self, selected_theme):
#         theme.applyTheme(self, selected_theme, 'plastique')
#
#     def getThemeBackgroundStyle(self):
#         '''Return the theme background color style. Can be overridden by child.'''
#         return 'default'
#
#     def is_docked(self):
#         raise NotImplementedError()
#
#     def pre_build(self):
#         '''Prepare general layout.'''
#         self.setLayout(QtWidgets.QVBoxLayout())
#         self.layout().setAlignment(QtCore.Qt.AlignTop)
#         if self.is_docked():
#             self.layout().setContentsMargins(0, 0, 0, 5)
#         else:
#             self.layout().setContentsMargins(16, 16, 16, 16)
#         self.layout().setSpacing(0)
#
#     def build(self):
#         '''Build widgets and parent them.'''
#         self.header = header.Header(self.session, parent=self)
#         self.layout().addWidget(self.header)
#         self.progress_widget = self.widget_factory.progress_widget
#         self.header.content_container.layout().addWidget(
#             self.progress_widget.widget
#         )
#
#         self.layout().addWidget(line.Line(style='solid', parent=self))
#
#         self.layout().addWidget(
#             self._build_context_selector(), QtCore.Qt.AlignTop
#         )
#
#         self.layout().addWidget(line.Line(parent=self))
#
#         self.host_and_definition_selector = self._build_definition_selector()
#         self.host_and_definition_selector.refreshed.connect(self.refresh)
#
#         self.scroll = scroll_area.ScrollArea()
#         self.scroll.setWidgetResizable(True)
#         self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
#
#         self.layout().addWidget(self.host_and_definition_selector)
#         self.layout().addWidget(self.scroll, 100)
#
#         self.layout().addWidget(self._build_button_widget())
#
#     def _build_context_selector(self):
#         '''Instantiate standard slave context selector'''
#         self.context_selector = ContextSelector(self.session, parent=self)
#         return self.context_selector
#
#     def _build_definition_selector(self):
#         raise NotImplementedError()
#
#     def _build_button_widget(self):
#         raise NotImplementedError()
#
#     def post_build(self):
#         '''Post Build ui method for events connections.'''
#         self.context_selector.entityChanged.connect(
#             self._on_context_selector_context_changed
#         )
#         self.host_and_definition_selector.hostChanged.connect(self.change_host)
#         self.host_and_definition_selector.definitionChanged.connect(
#             self.change_definition
#         )
#
#         if self.event_manager.mode == constants.LOCAL_EVENT_MODE:
#             self.host_and_definition_selector.host_widget.hide()
#
#         self._connect_run_button()
#
#     def _connect_run_button(self):
#         self.run_button.clicked.connect(self.run)
#
#     def _on_context_selector_context_changed(self, context_entity):
#         '''Updates the option dictionary with provided *context* when
#         entityChanged of context_selector event is triggered'''
#
#         self.set_context_id(context_entity['id'])
#
#         # Reset definition selector and clear client
#         self.host_and_definition_selector.clear_definitions()
#         self.host_and_definition_selector.populate_definitions()
#         self._clear_widget()
#
#     def set_context_id(self, context_id):
#         '''Set the context id for this client'''
#         if context_id and context_id != self.context_id:
#             discover_hosts = self.context_id is None
#             self.change_context(context_id)
#             if discover_hosts:
#                 self.add_hosts(self.discover_hosts())
#
#     def change_context(self, context_id):
#         """
#         Assign the given *context_id* as the current :obj:`context_id` and to the
#         :attr:`~ftrack_connect_pipeline.client.HostConnection.context_id` emit
#         on_context_change signal.
#         """
#         super(QtClient, self).change_context(context_id)
#         self.context_selector.set_context_id(self.context_id)
#         self.contextChanged.emit(context_id)
#
#     def add_hosts(self, host_connections):
#         '''
#         Adds the given *host_connections*
#
#         *host_connections* : list of
#         :class:`~ftrack_connect_pipeline.client.HostConnection`
#         '''
#         for host_connection in host_connections:
#             if host_connection in self.host_connections:
#                 continue
#             if self.context_id:
#                 host_connection.context_id = self.context_id
#             self._host_connections.append(host_connection)
#
#     def _host_discovered(self, event):
#         '''
#         Callback, add the :class:`~ftrack_connect_pipeline.client.HostConnection`
#         of the new discovered :class:`~ftrack_connect_pipeline.host.HOST` from
#         the given *event*.
#
#         *event*: :class:`ftrack_api.event.base.Event`
#         '''
#         super(QtClient, self)._host_discovered(event)
#         if self.definition_filter:
#             self.host_and_definition_selector.definition_title_filter = (
#                 self.definition_filter
#             )
#         if self.definition_extensions_filter:
#             self.host_and_definition_selector.definition_extensions_filter = (
#                 self.definition_extensions_filter
#             )
#         self.host_and_definition_selector.add_hosts(self.host_connections)
#
#     def _clear_widget(self):
#         if self.scroll and self.scroll.widget():
#             self.scroll.widget().deleteLater()
#
#     def change_host(self, host_connection):
#         '''Triggered when host_changed is called from the host_selector.'''
#         self._clear_widget()
#         super(QtClient, self).change_host(host_connection)
#         self.context_selector.host_changed(host_connection)
#
#     def change_definition(self, schema, definition, component_names_filter):
#         '''
#         Triggered when definition_changed is called from the host_selector.
#         Generates the widgets interface from the given *schema* and *definition*
#         '''
#         self._component_names_filter = component_names_filter
#         self._clear_widget()
#
#         if not schema and not definition:
#             self.definition_changed(None, 0)
#             return
#
#         super(QtClient, self).change_definition(schema, definition)
#
#         asset_type_name = definition['asset_type']
#
#         self.widget_factory.set_context(self.context_id, asset_type_name)
#         self.widget_factory.host_connection = self.host_connection
#         self.widget_factory.listen_widget_updates()
#         self.widget_factory.set_definition_type(self.definition['type'])
#         self.definition_widget = self.widget_factory.build_definition_ui(
#             self.definition, component_names_filter
#         )
#         self.scroll.setWidget(self.definition_widget)
#
#     def definition_changed(self, definition, available_components_count):
#         '''Can be overridden by child'''
#         pass
#
#     def _on_widget_asset_updated(self, asset_name, asset_id, is_valid):
#         if asset_id is None:
#             self.is_valid_asset_name = is_valid
#         else:
#             self.is_valid_asset_name = True
#
#     def _on_run_plugin(self, plugin_data, method):
#         '''Function called to run one single plugin *plugin_data* with the
#         plugin information and the *method* to be run has to be passed'''
#         self.run_plugin(plugin_data, method, self.engine_type)
#
#     def _open_assembler(self):
#         '''Open the assembler and close client if dialog'''
#         if not self.is_docked():
#             self.hide()
#         self.host_connection.launch_widget(core_constants.ASSEMBLER)
#
#     def run(self):
#         '''Function called when click the run button'''
#         self.widget_factory.has_error = False
#         serialized_data = self.widget_factory.to_json_object()
#         if not self.is_valid_asset_name:
#             msg = "Can't publish without a valid asset name"
#             self.widget_factory.progress_widget.set_status(
#                 constants.ERROR_STATUS, msg
#             )
#             self.logger.error(msg)
#             return False
#         engine_type = serialized_data['_config']['engine_type']
#         self.widget_factory.progress_widget.show_widget()
#         self.run_definition(serialized_data, engine_type)
#         return not self.widget_factory.has_error
#
#     def _on_components_checked(self, available_components_count):
#         self.definition_changed(self.definition, available_components_count)
#         self.run_button.setEnabled(available_components_count >= 1)
#         if available_components_count == 0:
#             self._clear_widget()
#
#     def _on_log_item_added(self, log_item):
#         if self.widget_factory:
#             self.widget_factory.update_widget(log_item)
#
#     def refresh(self):
#         '''Called upon definition selector refresh button click.'''
#         if self.widget_factory:
#             self.widget_factory.progress_widget.set_status_widget_visibility(
#                 False
#             )
#
#     def reset(self):
#         '''Reset a client that has become visible after being hidden.'''
#         self.set_context_id(ftrack_context_id())
#         self.host_and_definition_selector.refresh()
#
#     def conditional_rebuild(self):
#         if self._shown:
#             # Refresh when re-opened
#             self.host_and_definition_selector.refresh()
#         self._shown = True
#
#     def _launch_context_selector(self):
#         '''Close client (if not docked) and open entity browser.'''
#         if not self.is_docked():
#             self.hide()
#         self.host_connection.launch_widget(core_constants.CHANGE_CONTEXT)


# class QtDockedClient(QtClient, QtWidgets.QFrame):
#     '''Docked QT client'''
#
#     def __init__(self, event_manager, parent=None):
#         QtWidgets.QFrame.__init__(self, parent=parent)
#         QtClient.__init__(self, event_manager)


class RunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(RunButton, self).__init__(label, parent=parent)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)
