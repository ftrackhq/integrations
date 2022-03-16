# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants


class NukePublisherClient(QtPublisherClient):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]

    '''Dockable nuke publish widget'''

    def __init__(self, event_manager, unused_asset_list_model):
        super(NukePublisherClient, self).__init__(
            event_manager=event_manager,
            parent_window=QtWidgets.QApplication.activeWindow(),
        )
        self.setWindowTitle('Nuke Pipeline Publisher')

    def getThemeBackgroundStyle(self):
        return 'nuke'
