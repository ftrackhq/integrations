# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import JsonObject, JsonString


class HiddenObject(JsonObject):

    def __init__(self, name, schema_fragment, fragment_data,
                 previous_object_data, widget_factory, parent=None):
        super(HiddenObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )
        self.setVisible(False)

class HiddenString(JsonString):

    def __init__(self, name, schema_fragment, fragment_data,
                 previous_object_data, widget_factory, parent=None):
        super(HiddenString, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )
        self.setVisible(False)

