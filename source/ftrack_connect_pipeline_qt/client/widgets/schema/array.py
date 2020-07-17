# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget


class JsonArray(BaseJsonWidget):
    '''Widget representation of an array'''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise JsonArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(JsonArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        self.count = 0
        self.maxItems = self.schema_fragment.get('maxItems')

        self.innerLayout = QtWidgets.QVBoxLayout()

        if 'items' in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                if type(data) == dict:
                    name = data.get('name')
                else:
                    name = data
                obj = self.widget_factory.create_widget(
                    name, self.schema_fragment['items'], data,
                    self.previous_object_data
                )
                self.innerLayout.addWidget(obj)
                self.count += 1

        self.layout().addLayout(self.innerLayout)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        out = []
        for i in range(0, self.innerLayout.count()):
            widget = self.innerLayout.itemAt(i).widget()
            if 'to_json_object' in dir(widget):
                out.append(widget.to_json_object())
        return out

