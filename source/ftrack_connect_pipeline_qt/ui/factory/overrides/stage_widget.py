# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box


class GroupBoxStageWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a stage group box'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*,
        *fragment_data* and *parent*'''
        super(GroupBoxStageWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = group_box.GroupBox(self.name)
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)
