# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_maya.constants as maya_constants

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from ftrack_connect_pipeline_maya.utils.custom_commands import get_main_window


class QtMayaPublisherClient(QtPublisherClient):
    def __init__(self, event_manager, parent=None):
        '''Due to the Maya panel behaviour, we have to use *parent_window*
        instead of *parent*.'''
        super(QtMayaPublisherClient, self).__init__(
            event_manager, parent=get_main_window()
        )


class MayaPublisherClient(MayaQWidgetDockableMixin, QtMayaPublisherClient):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]

    '''Dockable maya publish widget'''

    def __init__(self, event_manager, unused_asset_list_model):
        super(MayaPublisherClient, self).__init__(event_manager=event_manager)
        self.setWindowTitle('ftrack Publisher')

    def getThemeBackgroundStyle(self):
        return 'maya'

    def show(self):
        super(MayaPublisherClient, self).show(
            dockable=True,
            floating=False,
            area='right',
            width=200,
            height=300,
            x=300,
            y=600,
        )
        QtPublisherClient.conditional_rebuild(self)
