# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client import change_context

from ftrack_connect_pipeline_3dsmax import utils as max_utils


class MaxQtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''Max change context dialog'''

    def __init__(self, event_manager, parent=None):
        super(MaxQtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent or max_utils.get_main_window()
        )

    def show(self):
        if super(MaxQtChangeContextClientWidget, self).show():
            max_utils.init_max(self.context_id, self.session)
