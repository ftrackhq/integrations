#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os

from ftrack_connect_pipeline_qt.client import QtClient
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import Dialog
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
        self.widget_factory = factory.WidgetFactory(
            event_manager, self.ui_types, self.client_name
        )
        super(QtOpenClient, self).__init__(event_manager, parent_window)
        self.logger.debug('start qt opener')

    def getThemeBackgroundStyle(self):
        return 'ftrack'

    def is_docked(self):
        raise False

    def post_build(self):
        super(QtOpenClient, self).post_build()
        self.context_selector.entityChanged.connect(self._store_global_context)

        self.widget_factory.widget_asset_updated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widget_run_plugin.connect(self._on_run_plugin)
        self.widget_factory.components_checked.connect(
            self._on_components_checked
        )

    def _store_global_context(self, entity):
        if os.environ.get('FTRACK_CONTEXTID') != entity['id']:
            os.environ['FTRACK_CONTEXTID'] = entity['id']
            self.logger.warning('Global context is now: {}'.format(entity))

    def change_definition(self, schema, definition, component_names_filter):
        self.run_button.setText('OPEN ASSEMBLER')
        super(QtOpenClient, self).change_definition(
            schema, definition, component_names_filter
        )

    def _on_components_checked(self, available_components_count):
        super(QtOpenClient, self).definition_changed(
            self.definition, available_components_count
        )
        self.run_button.setText(
            'OPEN' if available_components_count > 0 else 'OPEN ASSEMBLER'
        )
        self.run_button.setVisible(True)

    def definition_changed(self, definition, available_components_count):
        '''React upon change of definition, or no versions/components(definitions) available.'''
        if available_components_count == 0:
            # We have no definitions or nothing previously published
            self.ask_open_assembler = True
        elif definition is not None and available_components_count == 1:
            self.ask_open_latest = True

    def run(self):
        if self.definition is None:
            self.host_connection.launch_widget(qt_constants.ASSEMBLER_WIDGET)
            if not self.is_docked():
                self.get_parent_window().destroy()
                return
        super(QtOpenClient, self).run()
