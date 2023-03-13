# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject


class DefaultPluginContainerWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a container holding on or more schema plugins'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise DefaultPluginContainerWidgetObject with *name*,
        *fragment_data*, *previous_object_data* and *parent*'''
        super(DefaultPluginContainerWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)
