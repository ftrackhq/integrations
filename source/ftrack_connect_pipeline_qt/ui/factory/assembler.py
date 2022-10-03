# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import copy

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.factory.ui_overrides import (
    UI_OVERRIDES,
)

from ftrack_connect_pipeline_qt.ui.factory import (
    OpenerAssemblerWidgetFactoryBase,
)


class AssemblerWidgetFactory(OpenerAssemblerWidgetFactoryBase):
    '''Augmented widget factory for assembler(loader) client'''

    def __init__(self, event_manager, ui_types, parent=None):
        super(AssemblerWidgetFactory, self).__init__(
            event_manager,
            ui_types,
            parent=parent,
        )

    @staticmethod
    def client_type():
        return core_constants.LOADER

    @staticmethod
    def create_progress_widget(parent=None):
        '''(Override) Create the progress widget'''
        return OpenerAssemblerWidgetFactoryBase.create_progress_widget(
            AssemblerWidgetFactory.client_type(), parent=parent
        )

    def set_definition(self, definition):
        self.definition = definition

    def build(self, main_widget):
        '''(Override)'''

        # Create the components widget based on the definition
        self.components_obj = self.create_step_container_widget(
            self.definition, core_constants.COMPONENTS
        )

        main_widget.layout().addWidget(self.components_obj.widget)

        # Create the finalizers widget based on the definition
        finalizers_label = QtWidgets.QLabel('Finalizers')
        main_widget.layout().addWidget(finalizers_label)
        finalizers_label.setObjectName('h4')

        self.finalizers_obj = self.create_step_container_widget(
            self.definition, core_constants.FINALIZERS
        )

        main_widget.layout().addWidget(self.finalizers_obj.widget)

        if not UI_OVERRIDES.get(core_constants.FINALIZERS).get('show', True):
            self.finalizers_obj.hide()

        main_widget.layout().addStretch()

        # Check all components status of the current UI
        self.post_build()

        return main_widget

    def build_progress_ui(self, component):
        '''Build only progress widget components, prepare to run.'''

        types = [
            core_constants.CONTEXTS,
            core_constants.COMPONENTS,
            core_constants.FINALIZERS,
        ]

        for type_name in types:
            for step in self.definition[type_name]:
                step_type = step['type']
                step_name = step.get('name')
                if (
                    self.progress_widget
                    and step_type != 'finalizer'
                    and step.get('visible', True) is True
                ):
                    self.progress_widget.add_step(
                        step_type,
                        step_name,
                        version_id=component['version']['id'],
                    )
                for stage in step['stages']:
                    stage_name = stage.get('name')
                    if (
                        self.progress_widget
                        and step_type == 'finalizer'
                        and stage.get('visible', True) is True
                    ):
                        self.progress_widget.add_step(
                            step_type,
                            stage_name,
                            version_id=component['version']['id'],
                        )

    def check_components(self, asset_version_entity):
        '''(Override)'''
        if not self.components:
            # Wait for version to be selected and loaded
            return
        super(OpenerAssemblerWidgetFactoryBase, self).check_components(
            asset_version_entity
        )
