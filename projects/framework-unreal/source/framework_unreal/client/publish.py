# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from framework_core import constants as core_constants

from framework_qt.client.publish import QtPublisherClientWidget
import framework_qt.constants as qt_constants


import framework_unreal.constants as unreal_constants


class UnrealQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]
    '''Unreal single version publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(UnrealQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Unreal Pipeline Publisher')
        self.resize(600, 800)

    def get_theme_background_style(self):
        return 'ftrack'

    def is_docked(self):
        return False
