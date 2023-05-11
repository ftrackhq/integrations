# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_maya import utils as maya_utils


class MayaQtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''Maya change context dialog'''

    def __init__(self, event_manager, parent=None):
        super(MayaQtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )

    def show(self):
        if super(MayaQtChangeContextClientWidget, self).show():
            maya_utils.init_maya(self.context_id, self.session)
