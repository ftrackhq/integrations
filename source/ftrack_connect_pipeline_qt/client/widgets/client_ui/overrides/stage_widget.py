# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline_qt.client.widgets.client_ui import BaseUIWidget
from Qt import QtGui, QtCore, QtWidgets


class GroupBoxStageWidget(BaseUIWidget):
    '''Widget representation of a boolean'''
    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(GroupBoxStageWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QGroupBox(self.name)
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)
