#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client import QtClient
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.client import factory


class QtOpenClient(QtClient):
    '''
    Base open widget class.
    '''

    definition_filter = 'loader'
    client_name = qt_constants.OPEN_WIDGET

    def __init__(
        self,
        event_manager,
        parent_window,
        definition_extensions_filter=None,
    ):
        if not definition_extensions_filter is None:
            self.definition_extensions_filter = definition_extensions_filter
        self.ask_open_assembler = False
        self.ask_open_latest = False
        self._can_open = False
        self.widget_factory = factory.OpenerWidgetFactory(
            event_manager, self.ui_types, self.client_name
        )
        super(QtOpenClient, self).__init__(event_manager, parent_window)
        self.logger.debug('start qt opener')

    def getThemeBackgroundStyle(self):
        return 'ftrack'

    def is_docked(self):
        return False

    def post_build(self):
        super(QtOpenClient, self).post_build()
        self.context_selector.entityChanged.connect(self._set_context)

        self.widget_factory.widgetAssetUpdated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widgetRunPlugin.connect(self._on_run_plugin)
        self.widget_factory.componentsChecked.connect(
            self._on_components_checked
        )

    def _set_context(self, context, global_context_change):
        if not self.host_connection:
            return
        self.host_connection.set_context(context)
        if global_context_change:
            self.host_and_definition_selector.clear_definitions()
            self.host_and_definition_selector.populate_definitions()
            self._clear_widget()

    def change_definition(self, schema, definition, component_names_filter):
        self.run_button.setText('OPEN ASSEMBLER')
        self._can_open = False
        super(QtOpenClient, self).change_definition(
            schema, definition, component_names_filter
        )

    def _on_components_checked(self, available_components_count):
        super(QtOpenClient, self).definition_changed(
            self.definition, available_components_count
        )
        self._can_open = available_components_count > 0
        self.run_button.setText('OPEN' if self._can_open else 'OPEN ASSEMBLER')
        self.run_button.setVisible(True)

    def definition_changed(self, definition, available_components_count):
        '''React upon change of definition, or no versions/components(definitions) available.'''
        if available_components_count == 0:
            # We have no definitions or nothing previously published
            self.ask_open_assembler = True
        elif definition is not None and available_components_count >= 1:
            self.ask_open_latest = True

    def run(self):
        if not self._can_open:
            self.host_connection.launch_widget(qt_constants.ASSEMBLER_WIDGET)
            if not self.is_docked():
                self.get_parent_window().hide()
                self.get_parent_window().destroy()
            return
        if super(QtOpenClient, self).run():
            self.widget_factory.progress_widget.set_status(
                constants.SUCCESS_STATUS,
                'Successfully opened version!',
            )
