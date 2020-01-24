# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class JsonArray(BaseJsonWidget):
    """
        Widget representation of an array.
        Arrays can contain multiple objects of a type, or
        they can contain objects of specific types.
        We include a label and button for adding types.
    """
    def __init__(self, name, schema_fragment, fragment_data,
                 previous_object_data, widgetFactory, parent=None):
        super(JsonArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widgetFactory, parent=parent
        )

        self.count = 0
        self.maxItems = self.schema_fragment.get('maxItems')

        self.innerLayout = QtWidgets.QVBoxLayout()

        if "items" in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                name = data.get('name')
                obj = self.widget_factory.create_widget(
                    name, self.schema_fragment['items'], data,
                    self.previous_object_data
                )
                self.innerLayout.addWidget(obj)
                self.count += 1

        self.v_layout.addLayout(self.innerLayout)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def click_add(self):
        # TODO: Support array for "items"
        # TODO: Support additionalItems
        if "items" in self.schema_fragment:
            obj = self.widget_factory.create_widget(
                "Item #%d" % (self.count,), self.schema_fragment['items'],
                self.schema, self
            )
            self.count += 1
            self.vbox.addWidget(obj)

    def to_json_object(self):
        out = []
        for i in range(1, self.vbox.count()):
            widget = self.vbox.itemAt(i).widget()
            if "to_json_object" in dir(widget):
                out.append(widget.to_json_object())
        return out

