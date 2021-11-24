# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget
from Qt import QtWidgets


class DefaultStageWidget(BaseUIWidget):
    '''Widget representation of a boolean'''
    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(DefaultStageWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)
