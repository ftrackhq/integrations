# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.ui.factory import (
    OpenerAssemblerWidgetFactoryBase,
)


class OpenerWidgetFactory(OpenerAssemblerWidgetFactoryBase):
    '''Augmented widget factory for opener client'''

    def __init__(self, event_manager, ui_types, parent=None):
        super(OpenerWidgetFactory, self).__init__(
            event_manager, ui_types, parent=parent
        )
        self.progress_widget = OpenerWidgetFactory.create_progress_widget()

    @staticmethod
    def client_type():
        '''Return the type of client'''
        return core_constants.OPENER

    @staticmethod
    def create_progress_widget(parent=None):
        '''(Override)'''
        return OpenerAssemblerWidgetFactoryBase.create_progress_widget(
            OpenerWidgetFactory.client_type(), parent=parent
        )
