# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class JsonInteger(BaseJsonWidget):
    '''Widget representation of an integer'''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, context, parent=None
    ):
        '''Initialise JsonInteger with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(JsonInteger, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, context, parent=parent
        )

    def build(self):
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(self.name)
        self.spin  = QtWidgets.QSpinBox()

        self.label.setToolTip(self.description)


        hbox.addWidget(self.label)
        hbox.addWidget(self.spin)

        self.layout().addLayout(hbox)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        return self.spin.value()
