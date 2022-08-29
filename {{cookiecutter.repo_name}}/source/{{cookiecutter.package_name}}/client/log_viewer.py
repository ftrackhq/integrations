# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import log_viewer

from ftrack_connect_pipeline_{{cookiecutter.host_type}}.utils.custom_commands import get_main_window


class {{cookiecutter.host_type|capitalize}}QtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):
    '''{{cookiecutter.host_type|capitalize}} log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super({{cookiecutter.host_type|capitalize}}QtLogViewerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of {{cookiecutter.host_type|capitalize}}
        self.setWindowFlags(QtCore.Qt.Tool)
