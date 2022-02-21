#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client import QtClient
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.client import factory


class QtPublisherClient(QtClient):
    '''
    Base publish widget class.
    '''

    definition_filter = qt_constants.PUBLISH_WIDGET
    client_name = qt_constants.PUBLISH_WIDGET

    def __init__(self, event_manager, parent_window, parent=None):
        self.widget_factory = factory.WidgetFactory(
            event_manager, self.ui_types, self.client_name
        )
        super(QtPublisherClient, self).__init__(
            event_manager, parent_window, parent=parent
        )
        self.setWindowTitle('Standalone Pipeline Publisher')
        self.logger.debug('start qt publisher')

    def is_docked(self):
        raise True

    def pre_build(self):
        '''
        .. note::
            We want to hide the finalizers on the publisher but not on
            the loader, so we extend the schema_name_mapping dictionary.
        '''
        super(QtPublisherClient, self).pre_build()

    def post_build(self):
        super(QtPublisherClient, self).post_build()
        self.widget_factory.widget_asset_updated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widget_run_plugin.connect(self._on_run_plugin)
        self.widget_factory.components_checked.connect(
            self._on_components_checked
        )

    def change_definition(self, schema, definition, component_names_filter):
        self.run_button.setVisible(False)
        super(QtPublisherClient, self).change_definition(
            schema, definition, component_names_filter
        )

    def _on_components_checked(self, available_components_count):
        self.run_button.setText(self.client_name.upper())
        self.run_button.setVisible(available_components_count > 0)
        super(QtPublisherClient, self).definition_changed(
            self.definition, available_components_count
        )
