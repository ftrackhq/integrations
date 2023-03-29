# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_harmony.constants as harmony_constants


class HarmonyQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        harmony_constants.UI_TYPE,
    ]

    '''Dockable Harmony publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(HarmonyQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Harmony Pipeline Publisher')

    def get_theme_background_style(self):
        return 'ftrack'
