# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_houdini.utils.custom_commands import init_houdini


class HoudiniQtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''Houdini change context dialog'''

    def __init__(self, event_manager, parent=None):
        super(HoudiniQtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )

    def show(self):
        if super(HoudiniQtChangeContextClientWidget, self).show():
            init_houdini(self.context_id, self.session)
