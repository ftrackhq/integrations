# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.ui.factory import WidgetFactoryBase


class PublisherWidgetFactory(WidgetFactoryBase):
    '''Augmented widget factory for publisher client'''

    def __init__(self, event_manager, ui_types, parent=None):
        super(PublisherWidgetFactory, self).__init__(
            event_manager, ui_types, parent=parent
        )
        self.progress_widget = self.create_progress_widget(
            core_constants.PUBLISHER
        )

    @staticmethod
    def client_type():
        '''Return the type of client'''
        return core_constants.PUBLISHER

    def post_build(self):
        '''(Override)'''
        super(PublisherWidgetFactory, self).post_build()
        self.onQueryAssetVersionDone.emit(
            None
        )  # No asset to query, trigger component check

    def check_components(self, unused_asset_version_entity):
        '''(Override)'''
        available_components = 0
        try:
            if self.definition:
                available_components = len(
                    self.definition[core_constants.COMPONENTS]
                )
        finally:
            self.componentsChecked.emit(available_components)
