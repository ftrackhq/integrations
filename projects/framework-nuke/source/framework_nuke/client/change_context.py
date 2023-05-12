# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_qt.client import change_context
from framework_nuke import utils as nuke_utils


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
            nuke_utils.init_nuke(self.context_id, self.session)
