# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_{{cookiecutter.host_type}}.constants as {{cookiecutter.host_type}}_constants


class {{cookiecutter.host_type_capitalized}}QtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        {{cookiecutter.host_type}}_constants.UI_TYPE,
    ]
    '''Dockable {{cookiecutter.host_type}} asset manager widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        super({{cookiecutter.host_type_capitalized}}QtAssetManagerClientWidget, self).__init__(
            event_manager, asset_list_model, parent=parent
        )
        self.setWindowTitle('{{cookiecutter.host_type_capitalized}} Pipeline Asset Manager')

    def get_theme_background_style(self):
        return '{{cookiecutter.host_type}}'