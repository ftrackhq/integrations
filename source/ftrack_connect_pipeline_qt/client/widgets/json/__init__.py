# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets


class BaseJsonWidget(QtWidgets.QWidget):
    def __init__(
            self, name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=None
    ):
        super(BaseJsonWidget, self).__init__(parent=parent)
        # setup default vars
        self.widget_factory = widget_factory
        self.schema_fragment = schema_fragment
        self.fragment_data = fragment_data
        self.previous_object_data = previous_object_data

        # checks
        self.visible_properties = self.schema_fragment.get('order', [])
        self.name = name
        self.description = self.schema_fragment.get('description')
        self.properties = self.schema_fragment.get('properties')
        self._type = self.schema_fragment.get(
            "type", self.schema_fragment.get("$ref", "(?)"))

        # add default layout
        self.v_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.v_layout)


    def to_json_object(self):
        return {}


from ftrack_connect_pipeline_qt.client.widgets.json.array import JsonArray
from ftrack_connect_pipeline_qt.client.widgets.json.boolean import JsonBoolean
from ftrack_connect_pipeline_qt.client.widgets.json.integer import JsonInteger
from ftrack_connect_pipeline_qt.client.widgets.json.number import JsonNumber
from ftrack_connect_pipeline_qt.client.widgets.json.object import JsonObject
from ftrack_connect_pipeline_qt.client.widgets.json.string import JsonString
from ftrack_connect_pipeline_qt.client.widgets.json.unsupported import UnsupportedSchema