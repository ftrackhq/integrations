# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class UnsupportedSchema(BaseJsonWidget):
    '''Widget representation of an unsupported shcema element'''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise UnsupportedSchema with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(UnsupportedSchema, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        label = QtWidgets.QLabel(
            "(Unsupported schema entry: %s, %s)" % (self.name, self._type)
        )
        self.setStyleSheet("QLabel { font-style: italic; }")

        self.layout().addWidget(label)

    def to_json_object(self):
        return "(unsupported)"
