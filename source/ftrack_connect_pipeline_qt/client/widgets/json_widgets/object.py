# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtCore, QtWidgets


class JsonObject(QtWidgets.QGroupBox):
    """
        Widget representaiton of an object.
        Objects have properties, each of which is a widget of its own.
        We display these in a groupbox, which on most platforms will
        include a border.
    """
    def __init__(self, name, schema_fragment, fragment_data, previous_object_data,
                 widgetFactory, parent=None):
        QtWidgets.QGroupBox.__init__(self, name, parent)
        self.widget_factory = widgetFactory
        self.name = name
        self.fragment = schema_fragment
        self.vbox = QtWidgets.QVBoxLayout()
        self.innerLayout = QtWidgets.QVBoxLayout()
        #self.vbox.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.vbox)
        #self.setFlat(False)
        #self.layout().setContentsMargins(0, 0, 0, 0)
        self.visible_properties = []
        self.fragment_data = fragment_data
        self.previous_object_data = previous_object_data
        if self.previous_object_data:
            self.plugin_type = self.previous_object_data.get('name')


        if "title" in self.fragment:
            self.name = self.fragment['title']

        if "description" in self.fragment:
            self.setToolTip(self.fragment['description'])

        if "order" in self.fragment:
            self.visible_properties = self.fragment['order']

        self.properties = {}

        if "properties" not in self.fragment:
            label = QtWidgets.QLabel(
                "Invalid object description (missing properties)",
                self)
            label.setStyleSheet("QLabel { color: red; }")
            self.vbox.addWidget(label)
        else:
            if "widget" in self.fragment['properties'].keys():
                widget = self.widget_factory.fetch_plugin_widget(
                    self.fragment_data, self.plugin_type
                )
                self.innerLayout.addWidget(widget)
            else:
                for k, v in self.fragment['properties'].items():
                    if k in self.visible_properties:
                        newFragment_data = None
                        if self.fragment_data:
                            newFragment_data = self.fragment_data.get(k)
                        widget = self.widget_factory.create_widget(k, v,
                                                                   newFragment_data,
                                                                   self.fragment_data)
                        self.innerLayout.addWidget(widget)
                        self.properties[k] = widget
        self.vbox.addLayout(self.innerLayout)


    def to_json_object(self):
        out = {}
        for k, v in self.properties.items():
            out[k] = v.to_json_object()
        return out