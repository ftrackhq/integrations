# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget


class JsonObject(BaseJsonWidget):
    '''Widget representation of an object'''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise JsonObject with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(JsonObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        self.groupBox = QtWidgets.QGroupBox(self.name, self._parent)
        layout = QtWidgets.QVBoxLayout()
        self.innerLayout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.groupBox.setLayout(layout)
        self.groupBox.setFlat(False)
        self.groupBox.layout().setContentsMargins(0, 0, 0, 0)

        if self.previous_object_data:
            self.plugin_type = self.previous_object_data.get('name')

        self.groupBox.setToolTip(self.description)

        self.properties_widgets = {}

        if not self.properties:
            label = QtWidgets.QLabel(
                "Invalid object description (missing properties)",
                self)
            label.setStyleSheet("QLabel { color: red; }")
            layout.addWidget(label)
        else:
            if "widget" in self.properties.keys():
                widget = self.widget_factory.fetch_plugin_widget(
                    self.fragment_data, self.plugin_type
                )
                self.innerLayout.addWidget(widget)
            else:
                for k, v in self.properties.items():
                    new_fragment_data = None
                    if self.fragment_data:
                        new_fragment_data = self.fragment_data.get(k)
                    widget = self.widget_factory.create_widget(
                        k, v, new_fragment_data, self.fragment_data
                    )
                    self.innerLayout.addWidget(widget)
                    self.properties_widgets[k] = widget
        layout.addLayout(self.innerLayout)
        self.layout().addWidget(self.groupBox)

    def to_json_object(self):
        out = {}

        if "widget" in self.properties.keys():
            widget = self.widget_factory.get_registered_widget_plugin(
                self.fragment_data)
            out = widget.to_json_object()
            for k, v in self.fragment_data.items():
                if k not in out.keys():
                    out[k] = v
        else:
            for k, v in self.properties.items():
                widget = self.properties_widgets[k]
                out[k] = widget.to_json_object()
        return out
