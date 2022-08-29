# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_qt.client import change_context
from ftrack_connect_pipeline_cookiecutter.host_type}.utils.custom_commands import init_cookiecutter.host_type}


class {{cookiecutter.host_type|capitalize}}QtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''{{cookiecutter.host_type|capitalize}} change context dialog'''

    def __init__(self, event_manager, parent=None):
        super({{cookiecutter.host_type|capitalize}}QtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )

    def show(self):
        if super({{cookiecutter.host_type|capitalize}}QtChangeContextClientWidget, self).show():
            init_cookiecutter.host_type}(self.context_id, self.session)
