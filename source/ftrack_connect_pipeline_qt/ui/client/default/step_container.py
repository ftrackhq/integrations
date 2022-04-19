# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget


class DefaultStepContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(DefaultStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._widget = QtWidgets.QWidget(parent=self.parent())
        self.widget.setLayout(QtWidgets.QVBoxLayout())

    def build(self):
        pass
