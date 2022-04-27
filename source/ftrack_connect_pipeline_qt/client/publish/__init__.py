#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt import client
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt.ui.utility.widget import definition_selector


class QtPublisherClient(client.QtDockedClient):
    '''
    Base publish widget class.
    '''

    definition_filter = qt_constants.PUBLISHER_WIDGET

    def __init__(self, event_manager, parent=None):
        super(QtPublisherClient, self).__init__(event_manager, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')
        self.logger.debug('start qt publisher')

    def get_factory(self):
        return factory.PublisherWidgetFactory(
            self.event_manager,
            self.ui_types,
            parent=self.parent(),
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

    def _build_definition_selector(self):
        return definition_selector.PublisherDefinitionSelector(
            parent=self.parent()
        )

    def _build_button_widget(self):
        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().setContentsMargins(10, 10, 10, 5)
        button_widget.layout().setSpacing(10)

        self.run_button = client.RunButton('PUBLISH')
        button_widget.layout().addWidget(self.run_button)
        self.run_button.setEnabled(False)
        return button_widget

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

    def run(self):
        if super(QtPublisherClient, self).run():
            self.widget_factory.progress_widget.set_status(
                constants.SUCCESS_STATUS,
                'Successfully published {}!'.format(
                    self.definition['name'][
                        : self.definition['name'].rfind(' ')
                    ].lower()
                ),
            )
