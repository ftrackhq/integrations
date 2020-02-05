# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class JsonBoolean(BaseJsonWidget):
    '''Widget representation of a boolean'''
    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(JsonBoolean, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        self.checkbox = QtWidgets.QCheckBox()

        self.checkbox.setToolTip(self.description)

        self.layout().addWidget(self.checkbox)

    def to_json_object(self):
        return bool(self.isChecked())
