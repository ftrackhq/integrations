#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client import QtClient
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.client import factory


class QtPublisherClient(QtClient):
    '''
    Base publish widget class.
    '''

    definition_filter = qt_constants.PUBLISHER_WIDGET
    client_name = qt_constants.PUBLISHER_WIDGET

    def __init__(self, event_manager, parent_window, parent=None):
        super(QtPublisherClient, self).__init__(
            event_manager, parent_window, parent=parent
        )
        self.setWindowTitle('Standalone Pipeline Publisher')
        self.logger.debug('start qt publisher')

    def get_factory(self):
        return factory.PublisherWidgetFactory(
            self.event_manager,
            self.ui_types,
            self.client_name,
            parent=self.get_parent_window(),
        )

    def is_docked(self):
        return True

    def pre_build(self):
        '''
        .. note::
            We want to hide the finalizers on the publisher but not on
            the loader, so we extend the schema_name_mapping dictionary.
        '''
        super(QtPublisherClient, self).pre_build()

    def build(self):
        super(QtPublisherClient, self).build()
        self.run_button.setText('PUBLISH')

    def post_build(self):
        super(QtPublisherClient, self).post_build()
        self.widget_factory.widgetAssetUpdated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widgetRunPlugin.connect(self._on_run_plugin)
        self.widget_factory.componentsChecked.connect(
            self._on_components_checked
        )
        self.setMinimumWidth(300)

    def change_definition(self, schema, definition, component_names_filter):
        if not self._shown:
            self._postponed_change_definition = (
                schema,
                definition,
                component_names_filter,
            )
            return
        super(QtPublisherClient, self).change_definition(
            schema, definition, component_names_filter
        )

    def run(self, unused_method=None):
        if super(QtPublisherClient, self).run():
            self.widget_factory.progress_widget.set_status(
                constants.SUCCESS_STATUS,
                'Successfully published {}!'.format(
                    self.definition['name'][
                        : self.definition['name'].rfind(' ')
                    ].lower()
                ),
            )
