# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_houdini.constants as houdini_constants


class HoudiniQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        houdini_constants.UI_TYPE,
    ]

    '''Dockable houdini publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(HoudiniQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Houdini Pipeline Publisher')

    def get_theme_background_style(self):
        return 'houdini'
