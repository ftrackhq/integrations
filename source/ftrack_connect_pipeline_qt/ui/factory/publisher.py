# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.ui.factory.base import WidgetFactoryBase


class PublisherWidgetFactory(WidgetFactoryBase):
    def __init__(self, event_manager, ui_types, parent=None):
        super(PublisherWidgetFactory, self).__init__(
            event_manager, ui_types, parent=parent
        )
        self.progress_widget = self.create_progress_widget(
            core_constants.PUBLISHER, parent=self.parent()
        )

    @staticmethod
    def client_type():
        return core_constants.PUBLISHER

    def check_components(self, unused_asset_version_entity):
        available_components = 0
        try:
            if self.working_definition:
                available_components = len(
                    self.working_definition[core_constants.COMPONENTS]
                )
        finally:
            self.componentsChecked.emit(available_components)
