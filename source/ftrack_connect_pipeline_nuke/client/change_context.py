# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_nuke.utils.custom_commands import init_nuke


class NukeQtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''Nuke change context dialog'''

    def __init__(self, event_manager, parent=None):
        super(NukeQtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )

    def show(self):
        if super(NukeQtChangeContextClientWidget, self).show():
            init_nuke(self.context_id, self.session)
