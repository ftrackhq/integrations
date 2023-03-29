#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import shiboken2
from functools import partial

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client.loader import LoaderClient
from ftrack_connect_pipeline_qt.ui.utility.widget.button import (
    AddRunButton,
    LoadRunButton,
)

from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import ModalDialog
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    header,
    host_selector,
    definition_selector,
    line,
    tab,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.utils import clear_layout

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
from ftrack_connect_pipeline_qt.ui.assembler import (
    AssemblerDependenciesWidget,
    AssemblerBrowserWidget,
)
from ftrack_connect_pipeline_qt.ui.factory.assembler import (
    AssemblerWidgetFactory,
)


class QtLoaderClient(LoaderClient):
    '''
    Loader client class, as assembler is based on
    '''

    ui_types = [core_constants.UI_TYPE, qt_constants.UI_TYPE]

    def __init__(self, event_manager, multithreading_enabled=True):
        super(QtLoaderClient, self).__init__(
            event_manager, multithreading_enabled=multithreading_enabled
        )
        self.logger.debug('start qt loader')


class QtAssemblerClientWidget(QtLoaderClient, dialog.Dialog):
    '''
    Compound client dialog containing the assembler based on loader with the
    asset manager docked. Designed to ease to the load of dependencies and browsed
    assets into DCC.
    '''

    assembler_match_extension = (
        False  # Have assembler match on file extension (relaxed)
    )
    asset_fetch_chunk_size = (
        10  # Amount of assets to fetch at a time within the browser
    )

    # Assembler modes
    ASSEMBLE_MODE_DEPENDENCIES = 0
    ASSEMBLE_MODE_BROWSE = 1
    MODE_DEFAULT = ASSEMBLE_MODE_BROWSE

    contextChanged = QtCore.Signal(object)  # Context has changed

    def __init__(
        self,
        event_manager,
        modes,
        asset_list_model,
        multithreading_enabled=True,
        parent=None,
    ):
        '''
        Initialize the assembler client

        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param modes: Dictionary containing the load mode mapped functions
        :param asset_list_model: instance of :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel`

        :param parent:
        '''
        dialog.Dialog.__init__(self, parent=parent)
        QtLoaderClient.__init__(
            self, event_manager, multithreading_enabled=multithreading_enabled
        )

        self.logger.debug('start qt assembler')

        self.modes = modes
        self._asset_list_model = asset_list_model
        self.assemble_mode = (
            -1
        )  # The mode assembler is in - resolve dependencies or manual browse
        self._assembler_widget = None
        self.hard_refresh = True  # Flag telling assembler that next refresh should be a complete rebuild

        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        self.setProperty('docked', 'true' if self.is_docked() else 'false')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.pre_build()
        self.build()
        self.post_build()

        self.discover_hosts()

        self.setWindowTitle('ftrack Assembler')
        self.resize(1000, 500)

    def get_theme_background_style(self):
        return 'ftrack'

    def is_docked(self):
        return False

    # Build

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(16, 16, 16, 16)
        self.header = header.Header(self.session)
        # Create and add the asset manager client
        self.asset_manager = QtAssetManagerClientWidget(
            self.event_manager,
            self._asset_list_model,
            is_assembler=True,
            multithreading_enabled=self.multithreading_enabled,
        )

    def build_left_widget(self):
        '''Left split pane content'''

        self._left_widget = QtWidgets.QWidget()
        self._left_widget.setLayout(QtWidgets.QVBoxLayout())
        self._left_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._left_widget.layout().setSpacing(0)

        self.header.setMinimumHeight(45)
        self.header.setMaximumHeight(45)
        self._left_widget.layout().addWidget(self.header)

        self._left_widget.layout().addWidget(line.Line(style='solid'))

        self.progress_widget = AssemblerWidgetFactory.create_progress_widget()
        self.header.content_container.layout().addWidget(
            self.progress_widget.widget
        )

        # Have definition selector but invisible unless there are multiple hosts
        self.definition_selector = (
            definition_selector.AssemblerDefinitionSelector()
        )
        self.definition_selector.refreshed.connect(partial(self.refresh, True))
        self._left_widget.layout().addWidget(self.definition_selector)
        self.definition_selector.setVisible(False)

        # Have a tabbed widget for the different import modes

        self._tab_widget = AssemblerTabWidget()
        self._tab_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        # Build dynamically to save resources if lengthy asset lists

        self._dep_widget = QtWidgets.QWidget()
        self._dep_widget.setLayout(QtWidgets.QVBoxLayout())
        self._dep_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._dep_widget.layout().setSpacing(0)

        self._tab_widget.addTab(self._dep_widget, 'Suggestions')

        self._browse_widget = QtWidgets.QWidget()
        self._browse_widget.setLayout(QtWidgets.QVBoxLayout())
        self._browse_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._browse_widget.layout().setSpacing(0)

        self._tab_widget.addTab(self._browse_widget, 'Browse')

        self._left_widget.layout().setSpacing(5)
        self._left_widget.layout().addWidget(self._tab_widget)

        if self.MODE_DEFAULT == self.ASSEMBLE_MODE_DEPENDENCIES:
            # Set initial import mode, do not rebuild it as AM will trig it when it
            # has fetched assets
            self._tab_widget.setCurrentIndex(self.ASSEMBLE_MODE_DEPENDENCIES)
            self.set_assemble_mode(self.ASSEMBLE_MODE_DEPENDENCIES)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().setContentsMargins(2, 4, 8, 0)
        button_widget.layout().addStretch()
        button_widget.layout().setSpacing(2)
        self.run_button_no_load = AddRunButton('ADD TO SCENE')
        button_widget.layout().addWidget(self.run_button_no_load)
        self.run_button = LoadRunButton('LOAD INTO SCENE')
        self.run_button.setFocus()
        button_widget.layout().addWidget(self.run_button)
        self._left_widget.layout().addWidget(button_widget)

        self._asset_selection_updated()

        return self._left_widget

    def build_right_widget(self):
        '''Right split pane content'''

        self._right_widget = QtWidgets.QWidget()
        self._right_widget.setLayout(QtWidgets.QVBoxLayout())
        self._right_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._right_widget.layout().setSpacing(0)

        self.context_selector = ContextSelector(self.session)
        self._right_widget.layout().addWidget(
            self.context_selector, QtCore.Qt.AlignTop
        )

        self._right_widget.layout().addWidget(line.Line(style='solid'))

        self._right_widget.layout().addWidget(self.asset_manager, 100)

        return self._right_widget

    def build(self):
        '''Build assembler widget.'''

        # Create the host selector, usually hidden
        self.host_selector = host_selector.HostSelector(self)
        self.layout().addWidget(self.host_selector)

        # Create a splitter and add to client
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.build_left_widget())
        self.splitter.addWidget(self.build_right_widget())
        self.splitter.setHandleWidth(1)
        self.splitter.setSizes([600, 200])

        self.layout().addWidget(self.splitter, 100)

    def post_build(self):
        self.host_selector.hostChanged.connect(self.change_host)
        self.contextChanged.connect(self.on_context_changed_sync)
        self.definition_selector.definitionChanged.connect(
            self.change_definition
        )

        self.context_selector.changeContextClicked.connect(
            self._launch_context_selector
        )
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        self.asset_manager.assetsDiscovered.connect(self._on_assets_discovered)
        self.run_button.setFocus()
        self.run_button_no_load.clicked.connect(
            partial(self.run, "init_nodes")
        )
        self.run_button.clicked.connect(partial(self.run, "init_and_load"))

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        self.host_selector.add_hosts(host_connections)

    def on_host_changed(self, host_connection):
        '''Triggered when client has set host connection'''
        if self.definition_filters:
            self.definition_selector.definition_filters = (
                self.definition_filters
            )
        if self.definition_extensions_filter:
            self.definition_selector.definition_extensions_filter = (
                self.definition_extensions_filter
            )
        # Feed it to definition selector, to get schemas stored
        self.definition_selector.on_host_changed(host_connection)

    # Context

    def on_context_changed(self, context_id):
        '''Async call upon context changed'''
        self.contextChanged.emit(context_id)

    def on_context_changed_sync(self, context_id):
        '''(Override) Context has been set'''
        if not shiboken2.isValid(self):
            # Widget has been closed while context changed
            return
        self.context_selector.context_id = self.context_id
        # Have AM fetch assets
        self.asset_manager.on_host_changed(self.host_connection)
        # Reset definition selector and clear client
        self.definition_selector.clear_definitions()
        self.definition_selector.populate_definitions()
        if self.MODE_DEFAULT == self.ASSEMBLE_MODE_BROWSE:
            # Set initial import mode, do not rebuild it as AM will trig it when it
            # has fetched assets
            self._tab_widget.setCurrentIndex(self.ASSEMBLE_MODE_BROWSE)
            self.set_assemble_mode(self.ASSEMBLE_MODE_BROWSE)

    # Use

    def _on_assets_discovered(self):
        '''The assets in AM has been discovered, refresh at our end.'''
        self.refresh()

    def _on_components_checked(self, available_components_count):
        self.definition_changed(self.definition, available_components_count)
        self.run_button.setEnabled(available_components_count >= 1)

    def _on_tab_changed(self, index):
        self.set_assemble_mode(index)
        self.refresh(True)

    def set_assemble_mode(self, assemble_mode):
        if assemble_mode != self.assemble_mode:
            self.assemble_mode = assemble_mode
            active_tab_widget = (
                self._dep_widget
                if self.assemble_mode == self.ASSEMBLE_MODE_DEPENDENCIES
                else self._browse_widget
            )
            inactive_tab_widget = (
                self._dep_widget
                if self.assemble_mode != self.ASSEMBLE_MODE_DEPENDENCIES
                else self._browse_widget
            )
            # Clear the other tab
            clear_layout(inactive_tab_widget.layout())
            # Create tab widget
            self._assembler_widget = (
                AssemblerDependenciesWidget(self)
                if self.assemble_mode == self.ASSEMBLE_MODE_DEPENDENCIES
                else AssemblerBrowserWidget(self)
            )
            active_tab_widget.layout().addWidget(self._assembler_widget)
            self._assembler_widget.listWidgetCreated.connect(
                self._on_component_list_created
            )

    def _on_component_list_created(self, component_list):
        component_list.selectionUpdated.connect(self._asset_selection_updated)
        self._asset_selection_updated()

    def _asset_selection_updated(self, asset_selection=None):
        if self._assembler_widget is not None:
            loadable_count = self._assembler_widget.loadable_count
            s = ''
            if loadable_count > 0:
                if len(asset_selection or []) > 0:
                    s = ' {} ASSET{}'.format(
                        len(asset_selection),
                        'S' if len(asset_selection) > 1 else '',
                    )
                else:
                    s = ' ALL ASSETS'
            self.run_button_no_load.setText('ADD{} TO SCENE'.format(s))
            self.run_button_no_load.setEnabled(loadable_count > 0)
            self.run_button.setText('LOAD{} INTO SCENE'.format(s))
            self.run_button.setEnabled(loadable_count > 0)

    # Run

    def setup_widget_factory(self, widget_factory, definition, context_id):
        widget_factory.set_definition(definition)
        widget_factory.set_context(context_id, definition['asset_type'])
        widget_factory.host_connection = self._host_connection
        widget_factory.set_definition_type(definition['type'])

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def run(self, method=None):
        '''(Override) Function called when the run button is clicked.
        *method* decides which load method to use, "init_nodes"(track) or "init_and_load"(track and load)
        '''
        # Load batch of components, any selected
        component_widgets = self._assembler_widget.component_list.selection(
            as_widgets=True
        )
        if len(component_widgets) == 0:
            all_component_widgets = (
                self._assembler_widget.component_list.get_loadable()
            )
            if len(all_component_widgets) == 0:
                ModalDialog(
                    self, title='ftrack Assembler', message='No assets found!'
                )
                return
            if len(all_component_widgets) > 1:
                dlg = ModalDialog(
                    self,
                    title='ftrack Assembler',
                    question='{} all?'.format(
                        'Load' if method == 'init_and_load' else 'Track'
                    ),
                )
                if dlg.exec_():
                    # Select and use all loadable - having definition
                    component_widgets = all_component_widgets
            else:
                component_widgets = all_component_widgets
        if len(component_widgets) > 0:
            # Each component contains a definition ready to run and a factory,
            # run them one by one. Start by preparing progress widget
            self.progress_widget.prepare_add_steps()
            self.progress_widget.set_status(
                core_constants.RUNNING_STATUS, 'Initializing...'
            )
            for component_widget in component_widgets:
                component = self._assembler_widget.component_list.model.data(
                    component_widget.index
                )[0]
                factory = component_widget.factory
                factory.progress_widget = (
                    self.progress_widget
                )  # Have factory update main progress widget
                self.progress_widget.add_version(component)
                factory.build_progress_ui(component)
            self.progress_widget.widgets_added()

            self.progress_widget.show_widget()
            failed = 0
            for component_widget in component_widgets:
                # Prepare progress widget
                component = self._assembler_widget.component_list.model.data(
                    component_widget.index
                )[0]
                self.progress_widget.set_status(
                    core_constants.RUNNING_STATUS,
                    'Loading {} / {}...'.format(
                        str_version(component['version']), component['name']
                    ),
                )
                definition = component_widget.definition
                factory = component_widget.factory
                factory.listen_widget_updates()

                engine_type = definition['_config']['engine_type']
                try:
                    # Set method to importer plugins
                    if method:
                        for plugin in definition.get_all(
                            category=core_constants.PLUGIN,
                            type=core_constants.plugin._PLUGIN_IMPORTER_TYPE,
                        ):
                            plugin['default_method'] = method
                    self.run_definition(definition, engine_type)
                    # Did it go well?
                    if factory.has_error:
                        failed += 1
                finally:
                    component_widget.factory.end_widget_updates()

            succeeded = len(component_widgets) - failed
            if succeeded > 0:
                if failed == 0:
                    self.progress_widget.set_status(
                        core_constants.SUCCESS_STATUS,
                        'Successfully {} {}/{} asset{}!'.format(
                            'loaded'
                            if method == 'init_and_load'
                            else 'tracked',
                            succeeded,
                            len(component_widgets),
                            's' if len(component_widgets) > 1 else '',
                        ),
                    )
                else:
                    self.progress_widget.set_status(
                        core_constants.WARNING_STATUS,
                        'Successfully {} {}/{} asset{}, {} failed - check logs for more information!'.format(
                            'loaded'
                            if method == 'init_and_load'
                            else 'tracked',
                            succeeded,
                            len(component_widgets),
                            's' if len(component_widgets) > 1 else '',
                            failed,
                        ),
                    )
                self.asset_manager.asset_manager_widget.rebuild.emit()
            else:
                self.progress_widget.set_status(
                    core_constants.ERROR_STATUS,
                    'Could not {} asset{} - check logs for more information!'.format(
                        'load' if method == 'init_and_load' else 'tracked',
                        's' if len(component_widgets) > 1 else '',
                    ),
                )

    def refresh(self, force_hard_refresh=False):
        if force_hard_refresh:
            self.hard_refresh = True
        if self.hard_refresh:
            if self._assembler_widget:
                self._assembler_widget.rebuild()
            self.hard_refresh = False

    def _launch_assembler(self):
        '''Open the assembler and close client if dialog'''
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_client(qt_constants.ASSEMBLER_WIDGET)

    def _launch_publisher(self):
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_client(core_constants.PUBLISHER)

    def _launch_context_selector(self):
        '''Close client (if not docked) and open entity browser.'''
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_client(qt_constants.CHANGE_CONTEXT_WIDGET)

    def closeEvent(self, e):
        super(QtAssemblerClientWidget, self).closeEvent(e)
        self.logger.debug('closing qt client')
        # Unsubscribe to context change events
        self.unsubscribe_host_context_change()


class AssemblerTabWidget(tab.TabWidget):
    def __init__(self, parent=None):
        super(AssemblerTabWidget, self).__init__(parent=parent)
