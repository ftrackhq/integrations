# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject


class DefaultStepContainerWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a container hold one or more schema steps'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise DefaultStepContainerWidgetObject with *name*,
        *fragment_data*, *previous_object_data* and *parent*'''

        super(DefaultStepContainerWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._widget = QtWidgets.QWidget()
        self.widget.setLayout(QtWidgets.QVBoxLayout())

    def build(self):
        pass
