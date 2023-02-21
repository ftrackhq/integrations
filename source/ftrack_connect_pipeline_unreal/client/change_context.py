# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealQtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''Unreal change context dialog'''

    def __init__(self, event_manager, parent=None):
        super(UnrealQtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )
        # Make sure we become a proper window
        self.setWindowFlags(QtCore.Qt.Window)

    def show(self):
        if super(UnrealQtChangeContextClientWidget, self).show():
            unreal_utils.init_unreal(self.context_id, self.session)
