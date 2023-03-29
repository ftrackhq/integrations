# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from Qt import QtWidgets, QtCore

from {{cookiecutter.package_name}}.constants.asset import modes as load_const

from ftrack_connect_pipeline_qt.client import load
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import {{cookiecutter.package_name}}.constants as {{cookiecutter.host_type}}_constants
from {{cookiecutter.package_name}} import utils as {{cookiecutter.host_type}}_utils


class {{cookiecutter.host_type_capitalized}}QtAssemblerClientWidget(load.QtAssemblerClientWidget):
    '''{{cookiecutter.host_type_capitalized}} assembler dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        {{cookiecutter.host_type}}_constants.UI_TYPE,
    ]

    def __init__(self, event_manager, asset_list_model, parent=None):
        super({{cookiecutter.host_type_capitalized}}QtAssemblerClientWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
        )

        # Make sure we stays on top of {{cookiecutter.host_type_capitalized}}
        self.setWindowFlags(QtCore.Qt.Tool)
