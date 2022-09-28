# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import {{cookiecutter.package_name}}.constants as {{cookiecutter.host_type}}_constants


class {{cookiecutter.host_type_capitalized}}QtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        {{cookiecutter.host_type}}_constants.UI_TYPE,
    ]

    '''Dockable {{cookiecutter.host_type_capitalized}} publisher widget'''

    def __init__(self, event_manager, parent=None):
        super({{cookiecutter.host_type_capitalized}}QtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('{{cookiecutter.host_type_capitalized}} Pipeline Publisher')

    def get_theme_background_style(self):
        return '{{cookiecutter.host_type}}'
