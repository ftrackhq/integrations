#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import copy
import json
from functools import partial

from Qt import QtCore, QtWidgets

import qtawesome as qta

from ftrack_connect_pipeline.client import constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import Dialog
from ftrack_connect_pipeline_qt.client import QtClient

from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    definition_selector,
    line,
    tab,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.utils import str_version, clear_layout

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClient,
)

from ftrack_connect_pipeline_qt.ui.assembler.assembler import (
    AssemblerDependenciesWidget,
    AssemblerBrowserWidget,
)


class QtAssemblerClient(QtClient):
    '''
    Base assembler widget class, based on loader but without the definition
    selector and factorized widget builder.
    '''

    IMPORT_MODE_DEPENDENCIES = 0
    IMPORT_MODE_BROWSE = 1

    client_name = qt_constants.ASSEMBLER_WIDGET
    definition_filter = 'loader'

    import_mode = -1
    hard_refresh = True  # Flag telling assembler that next refresh should include dependency resolve

    def __init__(self, event_manager, modes, asset_list_model, parent_window):
        self.modes = modes
        self._asset_list_model = asset_list_model
        self.widget_factory = None
        super(QtAssemblerClient, self).__init__(event_manager, parent_window)
        self.logger.debug('start qt assembler')

    def getThemeBackgroundStyle(self):
        return 'ftrack'

    def is_docked(self):
        raise False

    def pre_build(self):
        super(QtAssemblerClient, self).pre_build()
        # Create and add the asset manager client
        self.asset_manager = QtAssetManagerClient(
            self.event_manager,
            self._asset_list_model,
            self.get_parent_window(),
            is_assembler=True,
        )

    def build(self):
        '''Build assembler widget.'''
        self.header = header.Header(self.session, title="Scene Assembler")
        self.layout().addWidget(self.header)

        self.progress_widget = factory.WidgetFactory.create_progress_widget(
            self.client_name
        )
        self.header.content_container.layout().addWidget(
            self.progress_widget.widget
        )

        self.context_selector = ContextSelector(self, self.session)
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        # Have definition selector but invisible unless there are multiple hosts
        self.host_and_definition_selector = (
            definition_selector.DefinitionSelectorButtons(self.client_name)
        )
        self.host_and_definition_selector.refreshed.connect(
            partial(self.refresh, True)
        )
        self.layout().addWidget(self.host_and_definition_selector)

        # self.layout().addWidget(line.Line())

        # Left split pane content

        self._left_widget = QtWidgets.QWidget()
        self._left_widget.setLayout(QtWidgets.QVBoxLayout())
        self._left_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._left_widget.layout().setSpacing(1)

        # Have a tabbed widget for the different import modes

        self._tab_widget = AssemblerTabWidget()

        # Build dynamically to save resources if lengthy asset lists

        self._dep_widget = QtWidgets.QWidget()
        self._dep_widget.setLayout(QtWidgets.QVBoxLayout())
        self._dep_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._dep_widget.layout().setSpacing(1)

        self._tab_widget.addTab(self._dep_widget, 'Suggestions')

        self._browse_widget = QtWidgets.QWidget()
        self._browse_widget.setLayout(QtWidgets.QVBoxLayout())
        self._browse_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._browse_widget.layout().setSpacing(1)

        self._tab_widget.addTab(self._browse_widget, 'Browse')

        self._left_widget.layout().addWidget(self._tab_widget)

        # Set initial import mode, do not rebuild it as AM will trig it when it
        # has resolved dependencies
        # self.set_import_mode(self.IMPORT_MODE_BROWSE)
        self._tab_widget.setCurrentIndex(self.IMPORT_MODE_DEPENDENCIES)
        self.set_import_mode(self.IMPORT_MODE_DEPENDENCIES)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().addStretch()
        self.run_button_no_load = AddRunButton('ADD TO SCENE')
        self.run_button_no_load.setMinimumHeight(32)
        button_widget.layout().addWidget(self.run_button_no_load)
        self.run_button = LoadRunButton('LOAD INTO SCENE')
        self.run_button.setMinimumHeight(32)
        self.run_button.setFocus()
        button_widget.layout().addWidget(self.run_button)
        self._left_widget.layout().addWidget(button_widget)

        # Right split pane content

        self._right_widget = QtWidgets.QWidget()
        self._right_widget.setLayout(QtWidgets.QVBoxLayout())
        self._right_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._right_widget.layout().setSpacing(1)

        self._right_widget.layout().addWidget(self.asset_manager, 100)

        # Create a splitter and add to client
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self._left_widget)
        self.splitter.addWidget(self._right_widget)
        self.layout().addWidget(self.splitter, 100)
        self.splitter.setSizes([500, 300])

    def post_build(self):
        super(QtAssemblerClient, self).post_build()
        self.host_and_definition_selector.hosts_discovered.connect(
            self._on_hosts_discovered
        )
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        self.asset_manager.assets_discovered.connect(self._assets_discovered)
        self.run_button.setFocus()
        self.run_button_no_load.clicked.connect(partial(self.run, True))
        self.run_button.setVisible(True)

    def _on_hosts_discovered(self, host_connects):
        self.host_and_definition_selector.setVisible(len(host_connects) > 1)

    def change_host(self, host_connection):
        super(QtAssemblerClient, self).change_host(host_connection)
        # Feed the host to the asset manager
        self.asset_manager.change_host(host_connection)

    def change_definition(self, schema, definition, component_names_filter):
        '''Not valid for assembler'''
        pass

    def _assets_discovered(self):
        '''The assets in AM has been discovered, refresh at our end.'''
        if self.hard_refresh:
            self.refresh()

    def _on_tab_changed(self, index):
        self.set_import_mode(index)
        self.refresh(True)

    def set_import_mode(self, import_mode):
        if import_mode != self.import_mode:
            self.import_mode = import_mode
            active_tab_widget = (
                self._dep_widget
                if self.import_mode == self.IMPORT_MODE_DEPENDENCIES
                else self._browse_widget
            )
            inactive_tab_widget = (
                self._dep_widget
                if self.import_mode != self.IMPORT_MODE_DEPENDENCIES
                else self._browse_widget
            )
            # Clear the other tab
            clear_layout(inactive_tab_widget.layout())
            self._assembler_widget = (
                AssemblerDependenciesWidget(self)
                if self.import_mode == self.IMPORT_MODE_DEPENDENCIES
                else AssemblerBrowserWidget(self)
            )
            active_tab_widget.layout().addWidget(self._assembler_widget)

    def refresh(self, force_hard_refresh=False):
        super(QtAssemblerClient, self).refresh()
        if force_hard_refresh:
            self.hard_refresh = True
        if self.hard_refresh:
            self._assembler_widget.rebuild()
            self.hard_refresh = False

    def reset(self):
        '''Assembler is shown again after being hidden.'''
        self.refresh(True)
        self.progress_widget.hide_widget()
        self.progress_widget.clear_components()

    def setup_widget_factory(self, widget_factory, definition, context_id):
        widget_factory.set_definition(definition)
        current_package = self.get_current_package(definition)
        widget_factory.set_context(
            context_id, current_package['asset_type_name']
        )
        widget_factory.host_connection = self._host_connection
        widget_factory.set_definition_type(definition['type'])
        widget_factory.set_package(current_package)

    def run(self, delayed_load=False):
        '''Function called when click the run button'''
        # Load batch of components, any selected
        component_widgets = self._assembler_widget.component_list.selection(
            as_widgets=True
        )
        if len(component_widgets) == 0:
            dlg = Dialog(
                self.get_parent_window(),
                title='ftrack Assembler',
                question='Load all?',
                prompt=True,
            )
            if dlg.exec_():
                # Select and use all loadable - having definition
                component_widgets = (
                    self._assembler_widget.component_list.get_loadable()
                )
        if len(component_widgets) > 0:
            # Each component contains a definition ready to run and a factory,
            # run them one by one. Start by preparing progress widget
            self.progress_widget.prepare_add_components()
            self.progress_widget.set_status(
                constants.RUNNING_STATUS, 'Initializing...'
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
            self.progress_widget.components_added()

            self.progress_widget.show_widget()
            failed = 0
            for component_widget in component_widgets:
                # Prepare progress widget
                component = self._assembler_widget.component_list.model.data(
                    component_widget.index
                )[0]
                self.progress_widget.set_status(
                    constants.RUNNING_STATUS,
                    'Loading {} / {}...'.format(
                        str_version(component['version']), component['name']
                    ),
                )
                definition = component_widget.definition
                factory = component_widget.factory
                factory.listen_widget_updates()

                engine_type = definition['_config']['engine_type']
                import json

                self.logger.info(
                    'Running definition: {}'.format(
                        json.dumps(definition, indent=4)
                    )
                )

                self.run_definition(definition, engine_type, delayed_load)
                # Did it go well?
                if factory.has_error:
                    failed += 1
                component_widget.factory.end_widget_updates()

            succeeded = len(component_widgets) - failed
            if succeeded > 0:
                if failed == 0:
                    self.progress_widget.set_status(
                        constants.SUCCESS_STATUS,
                        'Successfully {} {}/{} asset{}!'.format(
                            'loaded' if not delayed_load else 'tracked',
                            succeeded,
                            len(component_widgets),
                            's' if len(component_widgets) > 1 else '',
                        ),
                    )
                else:
                    self.progress_widget.set_status(
                        constants.WARNING_STATUS,
                        'Successfully {} {}/{} asset{}, {} failed - check logs for more information!'.format(
                            'loaded' if not delayed_load else 'tracked',
                            succeeded,
                            len(component_widgets),
                            's' if len(component_widgets) > 1 else '',
                            failed,
                        ),
                    )
                self.asset_manager.asset_manager_widget.rebuild.emit()
            else:
                self.progress_widget.set_status(
                    constants.ERROR_STATUS,
                    'Could not {} asset{} - check logs for more information!'.format(
                        'loaded' if not delayed_load else 'tracked',
                        's' if len(component_widgets) > 1 else '',
                    ),
                )


class AssemblerTabWidget(tab.TabWidget):
    def __init__(self, parent=None):
        super(AssemblerTabWidget, self).__init__(parent=parent)


class AddRunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(AddRunButton, self).__init__(label, parent=parent)
        # self.setIcon(qta.icon('mdi6.check', color='#5EAA8D'))


class LoadRunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(LoadRunButton, self).__init__(label, parent=parent)
        # self.setIcon(qta.icon('mdi6.check', color='#5EAA8D'))
