# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_harmony import utils as harmony_utils

class HarmonyQtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''Harmony change context dialog'''

    def __init__(self, event_manager, parent=None):
        super(HarmonyQtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )

    def show(self):
        if super(HarmonyQtChangeContextClientWidget, self).show():
            init_harmony(self.context_id, self.session)
