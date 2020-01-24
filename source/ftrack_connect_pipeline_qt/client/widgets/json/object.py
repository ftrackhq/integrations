# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class JsonObject(BaseJsonWidget):
    """
        Widget representaiton of an object.
        Objects have properties, each of which is a widget of its own.
        We display these in a groupbox, which on most platforms will
        include a border.
    """
    def __init__(self, name, schema_fragment, fragment_data,
                 previous_object_data, widgetFactory, parent=None):
        super(JsonObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widgetFactory, parent=parent
        )

        self.groupBox = QtWidgets.QGroupBox(self.name, parent)
        layout = QtWidgets.QVBoxLayout()
        self.innerLayout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.groupBox.setLayout(layout)
        self.groupBox.setFlat(False)
        self.groupBox.layout().setContentsMargins(0, 0, 0, 0)

        if self.previous_object_data:
            self.plugin_type = self.previous_object_data.get('name')

        self.name = self.schema_fragment.get('title', name)

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
                    if k in self.visible_properties:
                        new_fragment_data = None
                        if self.fragment_data:
                            new_fragment_data = self.fragment_data.get(k)
                        widget = self.widget_factory.create_widget(
                            k, v,new_fragment_data, self.fragment_data)
                        self.innerLayout.addWidget(widget)
                        self.properties_widgets[k] = widget
        layout.addLayout(self.innerLayout)
        #self.v_layout.addLayout(layout)
        self.v_layout.addWidget(self.groupBox)


    def to_json_object(self):
        out = {}
        for k, v in self.properties.items():
            out[k] = v.to_json_object()
        return out