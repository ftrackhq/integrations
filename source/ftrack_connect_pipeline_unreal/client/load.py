# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import shiboken2
from functools import partial

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.client import load
import ftrack_connect_pipeline_qt.constants as qt_constants

from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
import ftrack_connect_pipeline_unreal.constants as unreal_constants

from ftrack_connect_pipeline_qt.ui.utility.widget.button import (
    LoadRunButton,
    AddRunButton
)
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import ModalDialog
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    host_selector,
    definition_selector,
    line
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui.factory.assembler import (
    AssemblerWidgetFactory,
)

'''
############# IMPORTANT COMMENT ##############
If We want to activate the asset manager in the assembler, please remove all the 
code and only leave the init function without the asset_list_model=None and 
remove the self.refresh from it as well.

Suggestions are also deactivated as they also depend on the asset manager. 
(This should be cleaned up)
'''

class UnrealQtAssemblerClientWidget(load.QtAssemblerClientWidget):
    '''Unreal assembler dialog'''

    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]

    def __init__(
        self,
        event_manager,
        asset_list_model=None,# Set asset_list_model as Non to deactivate AM
        parent=None,
    ):
        super(UnrealQtAssemblerClientWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
            multithreading_enabled=False,
        )

        # Make sure we stays on top of Unreal
        self.setWindowFlags(QtCore.Qt.Window)

        # refresh assembler
        self.refresh()

    # Override pre_build to deactivate AM
    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(16, 16, 16, 16)
        self.header = header.Header(self.session)

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

        self._tab_widget = QtWidgets.QTabWidget()
        self._tab_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        # Build dynamically to save resources if lengthy asset lists

        self._dep_widget = QtWidgets.QWidget()
        self._dep_widget.setLayout(QtWidgets.QVBoxLayout())
        self._dep_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._dep_widget.layout().setSpacing(0)

        self._browse_widget = QtWidgets.QWidget()
        self._browse_widget.setLayout(QtWidgets.QVBoxLayout())
        self._browse_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._browse_widget.layout().setSpacing(0)

        self._tab_widget.addTab(self._browse_widget, 'Browse')

        self._left_widget.layout().setSpacing(5)
        self._left_widget.layout().addWidget(self._tab_widget)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().setContentsMargins(2, 4, 8, 0)
        button_widget.layout().addStretch()
        button_widget.layout().setSpacing(2)
        self.run_button = LoadRunButton('LOAD INTO SCENE')
        self.run_button.setFocus()
        button_widget.layout().addWidget(self.run_button)
        self._left_widget.layout().addWidget(button_widget)

        # Creating an unused button for consistency so we don't
        # have to override lot of methods.
        self.run_button_no_load = AddRunButton('ADD TO SCENE')

        # Creating context selector to be able to discover assets.
        # TODO: clean qt, why do we have to have context selector in the
        #  assembler if it works in a global context?
        self.context_selector = ContextSelector(self.session)

        self._asset_selection_updated()

        return self._left_widget

    def build(self):
        '''Build assembler widget.'''

        # Create the host selector, usually hidden
        self.host_selector = host_selector.HostSelector(self)
        self.layout().addWidget(self.host_selector)

        # Create a splitter and add to client
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.build_left_widget())
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
        self.run_button.setFocus()
        self.run_button.clicked.connect(partial(self.run, "init_and_load"))

    def on_context_changed_sync(self, context_id):
        '''(Override) Context has been set'''
        if not shiboken2.isValid(self):
            # Widget has been closed while context changed
            return
        self.context_selector.context_id = self.context_id
        # Reset definition selector and clear client
        self.definition_selector.clear_definitions()
        self.definition_selector.populate_definitions()
        if self.MODE_DEFAULT == self.ASSEMBLE_MODE_BROWSE:
            # Set initial import mode, do not rebuild it as AM will trig it when it
            # has fetched assets
            self._tab_widget.setCurrentIndex(self.ASSEMBLE_MODE_BROWSE)
            self.set_assemble_mode(self.ASSEMBLE_MODE_BROWSE)

    def run(self, method=None):
        '''(Override) Function called when the run button is clicked.
        *method* decides which load method to use, "init_nodes"(track) or "init_and_load"(track and load)'''
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
            else:
                self.progress_widget.set_status(
                    core_constants.ERROR_STATUS,
                    'Could not {} asset{} - check logs for more information!'.format(
                        'load' if method == 'init_and_load' else 'tracked',
                        's' if len(component_widgets) > 1 else '',
                    ),
                )