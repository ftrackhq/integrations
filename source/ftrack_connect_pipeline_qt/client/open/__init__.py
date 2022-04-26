#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client import QtClient
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


class QtOpenerClient(QtClient, dialog.Dialog):
    '''
    Base open widget class.
    '''

    definition_filter = 'opener'
    client_name = qt_constants.OPEN_WIDGET

    def __init__(
        self, event_manager, definition_extensions_filter=None, parent=None
    ):
        if not definition_extensions_filter is None:
            self.definition_extensions_filter = definition_extensions_filter

        dialog.Dialog.__init__(self, parent=parent)
        QtClient.__init__(self, event_manager)

        self.logger.debug('start qt opener')

        self.setWindowTitle('ftrack Open')
        self.resize(450, 530)

    def get_factory(self):
        return factory.OpenerWidgetFactory(
            self.event_manager,
            self.ui_types,
            self.client_name,
            parent=self.parent(),
        )

    def getThemeBackgroundStyle(self):
        return 'ftrack'

    def is_docked(self):
        return False

    def post_build(self):
        super(QtOpenerClient, self).post_build()
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
        super(QtOpenerClient, self).change_definition(
            schema, definition, component_names_filter
        )

    def definition_changed(self, definition, available_components_count):
        '''React upon change of definition, or no versions/components(definitions) available.'''
        self.run_button.setEnabled(
            definition is not None and available_components_count >= 1
        )

    def run(self, default_method=None):
        if super(QtOpenerClient, self).run():
            self.widget_factory.progress_widget.set_status(
                constants.SUCCESS_STATUS, 'Successfully opened version!'
            )

    def reset(self):
        '''Open dialog is shown again after being hidden.'''
        self.host_and_definition_selector.refresh()

    def show(self):
        if self._shown:
            # Widget has been shown before, reset client
            self._client.reset()
        super(QtOpenerClient, self).show()
        self._shown = True
