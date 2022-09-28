# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import log_viewer

from {{cookiecutter.package_name}}.utils.custom_commands import get_main_window


class {{cookiecutter.host_type_capitalized}}QtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):
    '''{{cookiecutter.host_type_capitalized}} log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super({{cookiecutter.host_type_capitalized}}QtLogViewerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of {{cookiecutter.host_type_capitalized}}
        self.setWindowFlags(QtCore.Qt.Tool)
