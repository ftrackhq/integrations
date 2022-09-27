# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_cookiecutter.host_type}.utils.custom_commands import init_cookiecutter.host_type}


class MaxQtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''Max change context dialog'''

    def __init__(self, event_manager, parent=None):
        super(MaxQtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )

    def show(self):
        if super(MaxQtChangeContextClientWidget, self).show():
            init_cookiecutter.host_type}(self.context_id, self.session)
