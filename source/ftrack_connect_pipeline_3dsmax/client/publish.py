# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_3dsmax.constants as 3dsmax_constants


class MaxQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        3dsmax_constants.UI_TYPE,
    ]

    '''Dockable Max publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(MaxQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Max Pipeline Publisher')

    def get_theme_background_style(self):
        return '3dsmax'
