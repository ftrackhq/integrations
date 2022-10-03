# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_qt.client import change_context
from {{cookiecutter.package_name}}.utils import custom_commands as {{cookiecutter.host_type}}_utils

class {{cookiecutter.host_type_capitalized}}QtChangeContextClientWidget(
    change_context.QtChangeContextClientWidget
):
    '''{{cookiecutter.host_type_capitalized}} change context dialog'''

    def __init__(self, event_manager, parent=None):
        super({{cookiecutter.host_type_capitalized}}QtChangeContextClientWidget, self).__init__(
            event_manager, parent=parent
        )

    def show(self):
        if super({{cookiecutter.host_type_capitalized}}QtChangeContextClientWidget, self).show():
            {{init_cookiecutter.host_type}}(self.context_id, self.session)
