# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_houdini import utils as houdini_utils


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
            houdini_utils.init_houdini(self.context_id, self.session)
