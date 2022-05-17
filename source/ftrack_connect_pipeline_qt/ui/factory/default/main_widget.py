# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject


class DefaultMainWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a boolean'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(DefaultMainWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QWidget(parent=self.parent())
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)

    def post_build(self):
        super(DefaultMainWidgetObject, self).post_build()
        self.widget.layout().setSpacing(0)
