# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from framework_qt.client.publish import QtPublisherClientWidget
import framework_core.constants as constants
import framework_qt.constants as qt_constants
import framework_houdini.constants as houdini_constants


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
