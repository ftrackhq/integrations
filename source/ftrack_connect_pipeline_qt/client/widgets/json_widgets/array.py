# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets


class JsonArray(QtWidgets.QWidget):
    """
        Widget representation of an array.
        Arrays can contain multiple objects of a type, or
        they can contain objects of specific types.
        We include a label and button for adding types.
    """
    def __init__(self, name, schema_fragment, fragment_data, plugin_type,
                 widgetFactory, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.widget_factory = widgetFactory
        self.name = name
        self.fragment = schema_fragment
        self.count = 0
        self.vbox = QtWidgets.QVBoxLayout()
        self.fragment_data = fragment_data
        self.maxItems = self.fragment.get('maxItems')

        self.innerLayout = QtWidgets.QVBoxLayout()
        if "items" in self.fragment and self.fragment_data:
            for data in self.fragment_data:
                name = data.get('name')
                obj = self.widget_factory.create_widget(
                    name, self.fragment['items'], data, plugin_type)
                self.innerLayout.addWidget(obj)
                self.count += 1

        self.vbox.addLayout(self.innerLayout)
        self.setLayout(self.vbox)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def click_add(self):
        # TODO: Support array for "items"
        # TODO: Support additionalItems
        if "items" in self.fragment:
            obj = self.widget_factory.create_widget("Item #%d" % (self.count,),
                                                    self.fragment['items'],
                                                    self.schema, self)
            self.count += 1
            self.vbox.addWidget(obj)

    def to_json_object(self):
        out = []
        for i in range(1, self.vbox.count()):
            widget = self.vbox.itemAt(i).widget()
            if "to_json_object" in dir(widget):
                out.append(widget.to_json_object())
        return out

class ComponentsArrayRepresentation(QtWidgets.QWidget):

    def __init__(self, name, schema_fragment, fragment_data, plugin_type,
                 widgetFactory, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.widget_factory = widgetFactory
        self.name = name
        self.fragment = schema_fragment
        self.fragment_data = fragment_data
        self.tabWidget = QtWidgets.QTabWidget()
        self.vbox = QtWidgets.QVBoxLayout()

        if "items" in self.fragment and self.fragment_data:
            for data in self.fragment_data:
                newTabWidget = QtWidgets.QWidget()
                widgetLayout = QtWidgets.QVBoxLayout()
                obj = self.widget_factory.create_widget(
                    data['name'], self.fragment['items'], data, plugin_type)
                widgetLayout.addWidget(obj)
                newTabWidget.setLayout(widgetLayout)
                self.tabWidget.addTab(newTabWidget, data["name"])

        self.vbox.addWidget(self.tabWidget)
        self.setLayout(self.vbox)
        self.layout().setContentsMargins(0, 0, 0, 0)
