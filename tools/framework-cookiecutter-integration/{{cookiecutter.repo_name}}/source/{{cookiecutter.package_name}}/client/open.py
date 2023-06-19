# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import open
import ftrack_connect_pipeline.constants as constants
import {{cookiecutter.package_name}}.constants as {{cookiecutter.host_type}}_constants
from ftrack_connect_pipeline_qt import constants as qt_constants


class {{cookiecutter.host_type_capitalized}}QtOpenerClientWidget(open.QtOpenerClientWidget):
    '''Open dialog and client'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        {{cookiecutter.host_type}}_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.mb']

    def __init__(self, event_manager, parent=None):
        super({{cookiecutter.host_type_capitalized}}QtOpenerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of {{cookiecutter.host_type_capitalized}}
        self.setWindowFlags(QtCore.Qt.Tool)
